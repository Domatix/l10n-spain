# -*- coding: utf-8 -*-
# Copyright 2016-2017 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

from odoo.addons.l10n_es_aeat_mod303.tests.test_l10n_es_aeat_mod303 \
    import TestL10nEsAeatMod303Base


class TestL10nEsAeatVatProrrate(TestL10nEsAeatMod303Base):
    @classmethod
    def setUpClass(cls):
        super(TestL10nEsAeatVatProrrate, cls).setUpClass()
        cls.journal = cls.env['account.journal'].create({
            'name': 'Test journal',
            'code': 'TEST',
            'type': 'general',
        })
        cls.account_type = cls.env['account.account.type'].create({
            'name': 'Test account type',
            'type': 'other',
        })
        cls.counterpart_account = cls.env['account.account'].create({
            'name': 'Test counterpart account',
            'code': 'COUNTERPART',
            'user_type_id': cls.account_type.id,
        })
        cls.prorrate_regul_account = cls.env['account.account'].search([
            ('code', 'like', '6391%'),
            ('company_id', '=', cls.model303.company_id.id),
        ], limit=1)
        if not cls.prorrate_regul_account:
            cls.prorrate_regul_account = cls.env['account.account'].create({
                'name': 'Test prorrate regularization account',
                'code': '6391000',
                'user_type_id': cls.account_type.id,
            })
        cls.model303.write({
            'vat_prorrate_type': 'general',
            'vat_prorrate_percent': 80,
            'journal_id': cls.journal.id,
            'counterpart_account_id': cls.counterpart_account.id,
        })
        cls.model303.button_calculate()
        cls.model303_4t = cls.model303.copy({
            'name': '9994000000303',
            'period_type': '4T',
            'date_start': '2017-09-01',
            'date_end': '2017-12-31',
            'vat_prorrate_type': 'general',
            'vat_prorrate_percent': 90,
        })
        cls.model303_4t.button_calculate()

    def test_deductable_part(self):
        self.assertEqual(self.model303.total_deducir, 2043.82)

    def test_regularization_move(self):
        self.model303.create_regularization_move()
        self.assertEqual(len(self.model303.move_id.line_ids), 82)
        lines = self.model303.move_id.line_ids
        line_counterpart = lines.filtered(
            lambda x: x.account_id == self.counterpart_account
        )
        self.assertEqual(line_counterpart.credit, 2126.98)
        # Final period
        self.assertEqual(self.model303_4t.casilla_44, 255.48)
        self.assertEqual(
            self.model303_4t.prorrate_regularization_account_id,
            self.prorrate_regul_account,
        )
        self.model303_4t.create_regularization_move()
        lines = self.model303_4t.move_id.line_ids
        line_prorrate_regularization = lines.filtered(
            lambda x: x.account_id == self.prorrate_regul_account
        )
        self.assertEqual(line_prorrate_regularization.credit, 255.48)
