# -*- coding: utf-8 -*-
# Copyright 2016-2017 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

from odoo.addons.l10n_es_aeat_mod303.tests.test_l10n_es_aeat_mod303 \
    import TestL10nEsAeatMod303Base


class TestL10nEsAeatVatProrrate(TestL10nEsAeatMod303Base):
    @classmethod
    def setUpClass(cls):
        super(TestL10nEsAeatVatProrrate, cls).setUpClass()
        cls.model303.write({
            'vat_prorrate_type': 'general',
            'vat_prorrate_percent': 80,
        })
        cls.model303.button_calculate()

    def test_deductable_part(self):
        self.assertEqual(self.model303.total_deducir, 2043.82)

    def test_regularization_move(self):
        journal = self.env['account.journal'].create({
            'name': 'Test journal',
            'code': 'TEST',
            'type': 'general',
        })
        account_type = self.env['account.account.type'].create({
            'name': 'Test account type',
            'type': 'other',
        })
        counterpart_account = self.env['account.account'].create({
            'name': 'Test counterpart account',
            'code': 'COUNTERPART',
            'user_type_id': account_type.id,
        })
        self.model303.write({
            'journal_id': journal.id,
            'counterpart_account': counterpart_account.id,
        })
        self.model303.create_regularization_move()
        self.assertEqual(len(self.model303.move_id.line_ids), 25)
        lines = self.model303.move_id.line_ids
        line_tax = lines.filtered(lambda x: x.account_id == self.account_tax)
        self.assertEqual(line_tax.credit, 40)
        line_counterpart = lines.filtered(
            lambda x: x.account_id == counterpart_account
        )
        self.assertEqual(line_counterpart.debit, 32)
        line_vat_prorrate_1 = lines.filtered(
            lambda x: (x.account_id == self.account_expense and
                       x.analytic_account_id == self.analytic_account_1)
        )
        self.assertEqual(line_vat_prorrate_1.debit, 2)
        line_vat_prorrate_2 = lines.filtered(
            lambda x: (x.account_id == self.account_expense and
                       x.analytic_account_id == self.analytic_account_2)
        )
        self.assertEqual(line_vat_prorrate_2.debit, 4)
        line_vat_prorrate_3 = lines.filtered(
            lambda x: (x.account_id == self.account_expense and
                       not x.analytic_account_id)
        )
        self.assertEqual(line_vat_prorrate_3.debit, 2)
