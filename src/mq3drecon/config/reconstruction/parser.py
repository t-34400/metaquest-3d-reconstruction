from dataclasses import fields, is_dataclass
from typing import Any, get_args, get_origin

from mq3drecon.config.reconstruction.device import DeviceSpec


def init_dataclass_from_dict(dc_cls: type, values: dict[str, Any], parent_device=None):
    kwargs = {}
    post_inits = {}

    for field_info in fields(dc_cls):
        if field_info.name not in values:
            continue

        value = _coerce_value(field_info.name, field_info.type, values[field_info.name], parent_device)

        if field_info.init:
            kwargs[field_info.name] = value
        else:
            post_inits[field_info.name] = value

    needs_device = any(is_device_field(field_info.name, field_info.type) for field_info in fields(dc_cls))
    if needs_device and "device" not in kwargs:
        if parent_device is None:
            raise ValueError(f"{dc_cls.__name__} requires 'device', but none was provided.")
        kwargs["device"] = parent_device

    instance = dc_cls(**kwargs)

    for key, value in post_inits.items():
        setattr(instance, key, value)

    return instance


def is_device_field(name: str, hint: Any) -> bool:
    return name == "device" and (hint is DeviceSpec or hint is Any or hint == "DeviceSpec")


def _coerce_value(name: str, hint: Any, value: Any, parent_device=None) -> Any:
    if is_device_field(name, hint):
        return str(value) if isinstance(value, str) else value
    if is_dataclass(hint) and isinstance(value, dict):
        return init_dataclass_from_dict(hint, value, parent_device=parent_device)
    if hint is float and isinstance(value, str):
        return float(value)
    if hint is int and isinstance(value, str):
        return int(value)
    if hint is bool and isinstance(value, str):
        return value.lower() in ("true", "1")
    if get_origin(hint) is list and isinstance(value, list):
        return _coerce_list(get_args(hint)[0], value)
    return value


def _coerce_list(subtype: Any, values: list[Any]) -> list[Any]:
    if subtype is float:
        return [float(value) for value in values]
    if subtype is int:
        return [int(value) for value in values]
    if subtype is str:
        return [str(value) for value in values]
    if subtype is bool:
        return [value.lower() in ("true", "1") if isinstance(value, str) else bool(value) for value in values]
    return values
