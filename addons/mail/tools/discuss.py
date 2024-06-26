# Part of Odoo. See LICENSE file for full copyright and licensing details.

import os
from collections import defaultdict

from odoo import models


def get_twilio_credentials(env) -> (str, str):
    """
    To be overridable if we need to obtain credentials from another source.
    :return: tuple(account_sid: str, auth_token: str)
    """
    params = env["ir.config_parameter"].sudo()
    account_sid = params.get_param("mail.twilio_account_sid")
    auth_token = params.get_param("mail.twilio_account_token")
    return account_sid, auth_token


def get_sfu_url(env) -> str | None:
    sfu_url = env['ir.config_parameter'].sudo().get_param("mail.sfu_server_url")
    if not sfu_url:
        sfu_url = os.getenv("ODOO_SFU_URL")
    if sfu_url:
        return sfu_url.rstrip("/")


def get_sfu_key(env) -> str | None:
    sfu_key = env['ir.config_parameter'].sudo().get_param('mail.sfu_server_key')
    if not sfu_key:
        return os.getenv("ODOO_SFU_KEY")
    return sfu_key


ids_by_model = defaultdict(lambda: ("id",))
ids_by_model.update(
    {
        "Persona": ("type", "id"),
        "Store": (),
        "Thread": ("model", "id"),
    }
)

target_model_by_model = {
    "discuss.channel": "Thread",
}


class Store:
    """Helper to build a dict of data for sending to web client.
    It supports merging of data from multiple sources, either through list extend or dict update.
    The keys of data are the name of models as defined in mail JS code, and the values are any
    format supported by store.insert() method (single dict or list of dict for each model name)."""

    def __init__(self, data=None, values=None):
        self.data = {}
        if data:
            self.add(data, values)

    def add(self, data, values=None):
        """Adds data to the store.
        data can be a recordset, in which case the model must have a _to_store() method.
        Or data can be a model name, in which case values must be a dict or list of dict.
        Or data can be a dict, in which case it is considered as values for the Store model.
        """
        if isinstance(data, models.Model):
            assert not values, f"expected empty values with recordset {data}: {values}"
            records = data
            model_name = target_model_by_model.get(records._name, records._name)
            values = records._to_store(self)
        elif isinstance(data, dict):
            assert not values, f"expected empty values with dict {data}: {values}"
            model_name = "Store"
            values = data
        else:
            model_name = data
        assert isinstance(model_name, str), f"expected str for model name: {model_name}: {values}"
        # skip empty values
        if not values:
            return self
        ids = ids_by_model[model_name]
        # handle singleton: update in place
        if len(ids) == 0:
            assert isinstance(values, dict), f"expected dict for singleton {model_name}: {values}"
            if not model_name in self.data:
                self.data[model_name] = {}
            self.data[model_name].update(values)
            return self
        # handle (multi) id(s): add or update existing
        if not model_name in self.data:
            self.data[model_name] = []
        if isinstance(values, dict):
            values = [values]
        assert isinstance(values, list), f"expected list for {model_name}: {values}"
        for vals in values:
            assert isinstance(vals, dict), f"expected dict for {model_name}: {vals}"
            for i in ids:
                assert vals.get(i), f"missing id {i} in {model_name}: {vals}"
            match = filter(lambda record: all(record[i] == vals[i] for i in ids), self.data[model_name])
            if record := next(match, None):
                record.update(vals)
            else:
                self.data[model_name].append(vals)
        return self

    def get_result(self):
        """Gets resulting data built from adding all data together."""
        return self.data
