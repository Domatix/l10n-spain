# -*- coding: utf-8 -*-
# © 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

import logging
from odoo.tests import common

_logger = logging.getLogger('aeat')


@common.at_install(False)
@common.post_install(True)
class TestL10nEsAeatModBase(common.SavepointCase):
    accounts = {}
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler aeat:DEBUG' in Odoo command line
    debug = False
    taxes_sale = {}
    taxes_purchase = {}
    taxes_result = {}

    @classmethod
    def _chart_of_accounts_create(cls):
        _logger.debug('Creating chart of account')
        cls.company = cls.env['res.company'].create({
            'name': 'Spanish test company',
        })
        cls.chart = cls.env.ref('l10n_es.account_chart_template_pymes')
        cls.env.ref('base.group_multi_company').write({
            'users': [(4, cls.env.uid)],
        })
        cls.env.user.write({
            'company_ids': [(4, cls.company.id)],
            'company_id': cls.company.id,
        })
        wizard = cls.env['wizard.multi.charts.accounts'].with_context(
            company_id=cls.company.id, force_company=cls.company.id
        ).create({
            'company_id': cls.company.id,
            'chart_template_id': cls.chart.id,
            'code_digits': 6,
            'currency_id': cls.env.ref('base.EUR').id,
            'transfer_account_id': cls.chart.transfer_account_id.id,
        })
        wizard.execute()
        return True

    @classmethod
    def _accounts_search(cls):
        _logger.debug('Searching accounts')
        codes = {'472000', '473000', '477000', '475100', '475000',
                 '600000', '700000', '430000', '410000'}
        for code in codes:
            cls.accounts[code] = cls.env['account.account'].search([
                ('company_id', '=', cls.company.id),
                ('code', '=', code),
            ])
        return True

    def _print_move_lines(self, lines):
        _logger.debug(
            '%8s %9s %9s %14s %s',
            'ACCOUNT', 'DEBIT', 'CREDIT', 'TAX', 'TAXES')
        for line in lines:
            _logger.debug(
                '%8s %9s %9s %14s %s',
                line.account_id.code, line.debit, line.credit,
                line.tax_line_id.description,
                line.tax_ids.mapped('description'))

    def _print_tax_lines(self, lines):
        for line in lines:
            _logger.debug(
                "=== [%s] ============================= [%s]",
                line.field_number, line.amount)
            self._print_move_lines(line.move_line_ids)

    @classmethod
    def _invoice_sale_create(cls, dt):
        data = {
            'company_id': cls.company.id,
            'partner_id': cls.customer.id,
            'date_invoice': dt,
            'type': 'out_invoice',
            'account_id': cls.customer.property_account_receivable_id.id,
            'journal_id': cls.journal_sale.id,
            'invoice_line_ids': [],
        }
        _logger.debug('Creating sale invoice: date = %s' % dt)
        if cls.debug:
            _logger.debug('%14s %9s' % ('SALE TAX', 'PRICE'))
        for desc, values in cls.taxes_sale.iteritems():
            if cls.debug:
                _logger.debug('%14s %9s' % (desc, values[0]))
            tax = cls.env['account.tax'].search([
                ('company_id', '=', cls.company.id),
                ('description', '=', desc),
            ])
            data['invoice_line_ids'].append((0, 0, {
                'name': 'Test for tax %s' % desc,
                'account_id': cls.accounts['700000'].id,
                'price_unit': values[0],
                'quantity': 1,
                'invoice_line_tax_ids': [(6, 0, [tax.id])],
            }))
        inv = cls.env['account.invoice'].create(data)
        inv.action_invoice_open()
        if cls.debug:
            cls._print_move_lines(inv.move_id.line_ids)
        return inv

    @classmethod
    def _invoice_purchase_create(cls, dt):
        data = {
            'company_id': cls.company.id,
            'partner_id': cls.supplier.id,
            'date_invoice': dt,
            'type': 'in_invoice',
            'account_id': cls.customer.property_account_payable_id.id,
            'journal_id': cls.journal_purchase.id,
            'invoice_line_ids': [],
        }
        _logger.debug('Creating purchase invoice: date = %s' % dt)
        if cls.debug:
            _logger.debug('%14s %9s' % ('PURCHASE TAX', 'PRICE'))
        for desc, values in cls.taxes_purchase.iteritems():
            if cls.debug:
                _logger.debug('%14s %9s' % (desc, values[0]))
            tax = cls.env['account.tax'].search([
                ('company_id', '=', cls.company.id),
                ('description', '=', desc),
            ])
            if not tax:
                _logger.error("Tax not found: {}".format(desc))
            data['invoice_line_ids'].append((0, 0, {
                'name': 'Test for tax %s' % tax,
                'account_id': cls.accounts['600000'].id,
                'price_unit': values[0],
                'quantity': 1,
                'invoice_line_tax_ids': [(6, 0, [tax.id])],
            }))
        inv = cls.env['account.invoice'].create(data)
        inv.action_invoice_open()
        if cls.debug:
            cls._print_move_lines(inv.move_id.line_ids)
        return inv

    @classmethod
    def _invoice_refund(cls, invoice, dt):
        _logger.debug('Refund %s invoice: date = %s' % (invoice.type, dt))
        inv = invoice.refund(date_invoice=dt, journal_id=cls.journal_misc.id)
        inv.action_invoice_open()
        if cls.debug:
            cls._print_move_lines(inv.move_id.line_ids)
        return inv

    @classmethod
    def _journals_create(cls):
        cls.journal_sale = cls.env['account.journal'].create({
            'company_id': cls.company.id,
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TSALE',
            'default_debit_account_id': cls.accounts['700000'].id,
            'default_credit_account_id': cls.accounts['700000'].id,
        })
        cls.journal_purchase = cls.env['account.journal'].create({
            'company_id': cls.company.id,
            'name': 'Test journal for purchase',
            'type': 'purchase',
            'code': 'TPUR',
            'default_debit_account_id': cls.accounts['600000'].id,
            'default_credit_account_id': cls.accounts['600000'].id,
        })
        cls.journal_misc = cls.env['account.journal'].create({
            'company_id': cls.company.id,
            'name': 'Test journal for miscellanea',
            'type': 'general',
            'code': 'TMISC',
        })
        return True

    @classmethod
    def _partners_create(cls):
        cls.customer = cls.env['res.partner'].create({
            'company_id': cls.company.id,
            'name': 'Test customer',
            'customer': True,
            'supplier': False,
            'property_account_payable_id': cls.accounts['410000'].id,
            'property_account_receivable_id': cls.accounts['430000'].id,
        })
        cls.supplier = cls.env['res.partner'].create({
            'company_id': cls.company.id,
            'name': 'Test supplier',
            'customer': False,
            'supplier': True,
            'property_account_payable_id': cls.accounts['410000'].id,
            'property_account_receivable_id': cls.accounts['430000'].id,
        })
        cls.customer_bank = cls.env['res.partner.bank'].create({
            'partner_id': cls.customer.id,
            'acc_number': 'ES66 2100 0418 4012 3456 7891',
        })
        return True

    @classmethod
    def setUpClass(cls):
        super(TestL10nEsAeatModBase, cls).setUpClass()
        # Create chart
        cls._chart_of_accounts_create()
        # Create accounts
        cls._accounts_search()
        # Create journals
        cls._journals_create()
        # Create partners
        cls._partners_create()
