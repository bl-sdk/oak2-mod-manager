# Changelog

## v0.3: Whiskey Foxtrot
- Upgraded to Python 3.14.

### [Mods Base v1.12](https://github.com/bl-sdk/mods_base/blob/master/Readme.md#v112)
> - Deprecated `ValueOption.on_change`, as well as setting it via `__call__`, in favour of separate,
>   more explicit, `on_change_anytime` and `on_change_while_enabled` callbacks.
>
> - Added a `HookType.pause()` context manager. This may sometimes be preferable over the
>   `unrealsdk.hooks.prevent_hooking_direct_calls()` context manager.

### [pyunrealsdk v1.10.0](https://github.com/bl-sdk/pyunrealsdk/blob/master/changelog.md#v1100)
> - Improved support for the custom BL4 types - `FGameDataHandle`, `FGbxDefPtr`, `FGbxInlineStruct`,
>   and their associated properties.

### [unrealsdk v3.2.0](https://github.com/bl-sdk/unrealsdk/blob/master/changelog.md#320)
> - Updated to support both sets of BL4 signatures, optimized sigscanning.
>
> - Improved support for the custom BL4 types - `FGameDataHandle`, `FGbxDefPtr`, `FGbxInlineStruct`,
>   and their associated properties.

## Beta v0.2: Valuepalooza
(This release was later withdrawn in favour of v0.1, due to gearbox removing the optimizations that
necessitated it)

- Updated to support the latest version of the game (Mad Ellie)

### Keybinds v1.1
- Updated to support the latest version of the game

### pyunrealsdk v1.9.1
> - Assigning one wrapped array to another with a compatible, but different, property, will now
>   automatically do the "convert to list" workaround for you.

### unrealsdk v3.1.0
> - Updated to support the latest Borderlands 4 update. Thanks to Cr4nkSt4r for help finding new
>   signatures.

## Beta v0.1: Sprezzatura
- Initial Release
