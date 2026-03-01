#include "pyunrealsdk/pch.h"
#include "pyunrealsdk/debugging.h"
#include "pyunrealsdk/hooks.h"
#include "pyunrealsdk/logging.h"
#include "pyunrealsdk/static_py_object.h"
#include "pyunrealsdk/unreal_bindings/uenum.h"
#include "unrealsdk/memory.h"
#include "unrealsdk/unreal/class_name.h"
#include "unrealsdk/unreal/classes/uenum.h"
#include "unrealsdk/unreal/classes/uobject.h"
#include "unrealsdk/unreal/classes/uobject_funcs.h"
#include "unrealsdk/unreal/properties/zboolproperty.h"
#include "unrealsdk/unreal/structs/fname.h"
#include "unrealsdk/unrealsdk.h"

using namespace unrealsdk::unreal;
using namespace unrealsdk::memory;

namespace {

using EInputEvent = uint32_t;
using UGbxEnhancedPlayerInput = UObject;

// NOLINTBEGIN(cppcoreguidelines-pro-type-member-init, readability-identifier-naming,
//             readability-magic-numbers)

struct FKey {
    FName KeyName;
    uint8_t _KeyDetails[0x10];
};

struct FInputDeviceId {
    int InternalId;
};

struct FInputKeyParams {
    FKey Key;
    FInputDeviceId InputDevice;
    EInputEvent Event;
    int32_t NumSamples;
    float32_t DeltaTime;
    uint8_t Delta[0x18];
    bool bIsGamepadOverride;
};

// NOLINTEND(cppcoreguidelines-pro-type-member-init, readability-identifier-naming,
//           readability-magic-numbers)

pyunrealsdk::StaticPyObject input_event_enum = pyunrealsdk::unreal::enum_as_py_enum(
    validate_type<UEnum>(unrealsdk::find_object(L"Enum", L"/Script/Engine.EInputEvent")));

std::atomic<uintptr_t> global_handle = 1;

struct PY_OBJECT_VISIBILITY KeybindData {
    pyunrealsdk::StaticPyObject callback;
    std::optional<EInputEvent> event;
    uintptr_t handle;
};

std::unordered_multimap<FName, KeybindData> all_keybinds{};

/**
 * @brief Processes a key event.
 *
 * @param self The player input object triggering the event.
 * @param params The input params.
 * @return True if to block the key event.
 */
bool handle_key_event(UGbxEnhancedPlayerInput* self, FInputKeyParams* params) {
    // Check we have a matching keybind
    const auto equal_range = all_keybinds.equal_range(params->Key.KeyName);
    const auto with_matching_key = std::ranges::subrange(equal_range.first, equal_range.second);
    if (with_matching_key.empty()) {
        return false;
    }

    // Check we have a matching event. Doing this after menu since I expect typically we
    const auto input_event = params->Event;
    auto with_matching_event =
        with_matching_key | std::views::filter([input_event](const auto& ittr) {
            const auto& data = ittr.second;
            return !data.event.has_value() || data.event == input_event;
        });
    if (with_matching_event.empty()) {
        return false;
    }

    // Check we're not in a menu
    static const auto pc_class = validate_type<UClass>(
        unrealsdk::find_object(L"Class", L"/Script/OakGame.OakPlayerController"));
    auto player_controller = self->Outer();
    if (player_controller == nullptr || !player_controller->is_instance(pc_class)) {
        // Should be impossible?
        return false;
    }
    // This seems a a bit wrong but does seem to work, even on controller
    static auto show_mouse_cursor =
        validate_type<ZBoolProperty>(pc_class->find_prop(L"bShowMouseCursor"_fn));
    auto is_in_menu = player_controller->get<ZBoolProperty>(show_mouse_cursor);
    if (is_in_menu) {
        return false;
    }

    const py::gil_scoped_acquire gil{};

    // We're definitely going to run the python callbacks now.
    // Copy into a new vector so if the callback removes itself it doesn't screw up iteration.
    std::vector<decltype(all_keybinds)::value_type> matching_binds{};
    std::ranges::copy(with_matching_event, std::back_inserter(matching_binds));

    // We might be able to get away with skipping creating this enum, saves us some more time.
    py::object event_as_enum{};

    bool should_block = false;

    const auto safe_run_callback = [&should_block](auto lambda) {
        try {
            auto ret = lambda();
            if (pyunrealsdk::hooks::is_block_sentinel(ret)) {
                should_block = true;
            }
        } catch (const py::error_already_set& ex) {
            pyunrealsdk::logging::log_python_exception(ex);
        } catch (const std::exception& ex) {
            LOG(ERROR, "Exception in keybind hook: {}", ex.what());
        } catch (...) {
            LOG(ERROR, "Unknown exception in keybind hook");
        }
    };

    pyunrealsdk::debug_this_thread();

    for (const auto& bind : matching_binds) {
        if (!bind.second.event.has_value()) {
            if (!event_as_enum) {
                event_as_enum = input_event_enum(input_event);
            }

            safe_run_callback(
                [&bind, &event_as_enum]() { return bind.second.callback(event_as_enum); });
        } else if (bind.second.event.value() == input_event) {
            safe_run_callback([&bind]() { return bind.second.callback(); });
        }
    }

    return should_block;
}

using playerinput_inputkey_func = uintptr_t (*)(UGbxEnhancedPlayerInput* self,
                                                FInputKeyParams* params);
playerinput_inputkey_func playerinput_inputkey_ptr;

const constinit Pattern<57> PLAYERINPUT_INPUTKEY_PATTERN{
    "41 57"                // push r15
    "41 56"                // push r14
    "41 54"                // push r12
    "56"                   // push rsi
    "57"                   // push rdi
    "55"                   // push rbp
    "53"                   // push rbx
    "48 81 EC ????????"    // sub rsp, 000000A0
    "0F29 BC 24 ????????"  // movaps [rsp+00000090], xmm7
    "0F29 B4 24 ????????"  // movaps [rsp+00000080], xmm6
    "48 89 D7"             // mov rdi, rdx
    "48 89 CE"             // mov rsi, rcx
    "48 8B 05 ????????"    // mov rax, [Borderlands4.exe+C499940]
    "48 31 E0"             // xor rax, rsp
    "48 89 44 24 ??"       // mov [rsp+78], rax
    "48 89 D1"             // mov rcx, rdx
};

uintptr_t playerinput_inputkey_hook(UGbxEnhancedPlayerInput* self, FInputKeyParams* params) {
    try {
        if (handle_key_event(self, params)) {
            return 1;
        }
    } catch (const std::exception& ex) {
        LOG(ERROR, "Exception in keybind hook: {}", ex.what());
    } catch (...) {
        LOG(ERROR, "Unknown exception in keybind hook");
    }
    return playerinput_inputkey_ptr(self, params);
}

}  // namespace

// NOLINTNEXTLINE(readability-identifier-length)
PYBIND11_MODULE(keybinds, m) {
    detour(PLAYERINPUT_INPUTKEY_PATTERN.sigscan_nullable(), playerinput_inputkey_hook,
           &playerinput_inputkey_ptr, "UGbxEnhancedPlayerInput::InputKey");

    m.def(
        "register_keybind",
        [](FName key, const std::optional<EInputEvent>& event,
           const py::object& callback) -> void* {
            auto handle = global_handle++;
            all_keybinds.emplace(std::piecewise_construct, std::forward_as_tuple(key),
                                 std::forward_as_tuple(callback, event, handle));
            // Return as a void* so pybind turns them into a capsule, rather than leaving as an int
            return reinterpret_cast<void*>(handle);
        },
        "Registers a new keybind.\n"
        "\n"
        "If an event is given, the callback will only match that event, and will be\n"
        "called with no args. Otherwise, it will be called on every key event, with the\n"
        "event passed as an arg.\n"
        "\n"
        "The callback may return the sentinel `Block` type (or an instance thereof) in\n"
        "order to block normal processing of the key event.\n"
        "\n"
        "Args:\n"
        "    key: The key to match, or None to match any.\n"
        "    event: The key event to match, or None to match any.\n"
        "    callback: The callback to use.\n"
        "Returns:\n"
        "    An opaque handle to be used in calls to deregister_keybind.\n",
        "key"_a, "event"_a, "callback"_a);

    m.def(
        "deregister_keybind",
        [](void* handle) {
            auto handle_int = reinterpret_cast<uintptr_t>(handle);
            std::erase_if(all_keybinds, [handle_int](const auto& entry) {
                const auto& [key, data] = entry;
                return data.handle == handle_int;
            });
        },
        "Removes a previously registered keybind.\n"
        "\n"
        "Does nothing if the passed handle is invalid.\n"
        "\n"
        "Args:\n"
        "    handle: The handle returned from `register_keybind`.\n",
        "handle"_a);

    m.def(
        "_deregister_by_key",
        [](FName& key) {
            std::erase_if(all_keybinds, [key](const auto& entry) {
                const auto& [key_in_map, data] = entry;
                return key_in_map == key;
            });
        },
        "Deregisters all keybinds matching the given key.\n"
        "\n"
        "Not intended for regular use, only exists for recovery during debugging, in case\n"
        "a handle was lost.\n"
        "\n"
        "Args:\n"
        "    key: The key to remove all keybinds of.\n");

    m.def(
        "_deregister_all", []() { all_keybinds.clear(); },
        "Deregisters all keybinds.\n"
        "\n"
        "Not intended for regular use, only exists for recovery during debugging, in case\n"
        "a handle was lost.\n");
}
