
from odoo import fields
from odoo.exceptions import UserError  
from odoo.tests import Form
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


@tagged("post_install", "-at_install")
class TestAccountTierValidation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context={**cls.env.context, **DISABLED_MAIL_CONTEXT})

        cls.reviewer = cls.env["res.users"].create({
            "name": "SpearHead",
            "login": "spearhead",
            "email": "spearhear@gmail.com",
        })

    def test_01_tier_definition_models(self):
        res = self.env["tier.definition"]._get_tier_validation_model_names()
        self.assertIn("account.move", res)

    def test_02_form(self):
        for _type in ("in_invoice", "out_invoice", "in_refund", "out_refund"):
            self.env["tier.definition"].create(
                {
                    "model_id": self.env["ir.model"]
                    .search([("model", "=", "account.move")])
                    .id,
                    "definition_domain": f"[('move_type', '=', '{_type}')]",
                }
            )
            with Form(
                self.env["account.move"].with_context(default_move_type=_type)
            ) as form:
                form.save()
                self.assertTrue(form.hide_post_button)

    def test_03_move_post(self):
        for _type in ("in_invoice", "out_invoice", "in_refund", "out_refund"):
            self.env["tier.definition"].create({
                "name": f"Test Tier {_type}",
                "model_id": self.env["ir.model"]
                .search([("model", "=", "account.move")])
                .id,
                "definition_domain": f"[('move_type', '=', '{_type}')]",
                "review_type": "individual",
                "reviewer_ids": [(6, 0, [self.reviewer.id])],
                "sequence": 10,
            })
            move = self.env["account.move"].create({
                "move_type": _type,
                "partner_id": self.env["res.partner"].create({"name": "Test"}).id,
            })
            with self.assertRaises(UserError):  
                move.action_post()