import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

# Never use deployment credentials, or allow real network calls in this suite.
os.environ.update(BOT_TOKEN='123456:LOCAL_TEST_TOKEN', USERS='101,202', BASE_URL='https://example.invalid')
from src.parser import main as parser
from src.parser.parser import InvalidSearchPage, parse_data
from src.parser import fetcher
from src.bot import bot as app
import requests

EMPTY = '<table id="search-result"><tbody></tbody></table>'
ROW = '<tr><td>1</td><td><a href="/announce/index/1">пошив</a></td><td><strong>ткань</strong></td><td></td><td><strong>100</strong></td><td>Конкурс</td></tr>'
PAGE = '<table id="search-result"><tbody>' + ROW + '</tbody></table>'
CARD = '<div class="form-group"><label>Срок окончания</label><input class="form-control" value="20.11.2026"></div>'
LOT = dict(lot_code='1', title='пошив', price=100, customer='Заказчик', link='https://example.invalid/1')


class NetworkBlocked(unittest.TestCase):
    def setUp(self):
        p = patch('socket.socket.connect', side_effect=AssertionError('Network forbidden'))
        p.start()
        self.addCleanup(p.stop)


class HtmlTests(NetworkBlocked):
    def test_empty_table_is_end(self):
        self.assertEqual(parse_data(EMPTY), [])

    def test_invalid_html_is_not_end(self):
        for html in ['<html>error</html>', '<table id="search-result"></table>', EMPTY.replace('</tbody>', '<tr><td>broken</td></tr></tbody>'), PAGE.replace('href="/announce/index/1"', '')]:
            with self.subTest(html=html), self.assertRaises(InvalidSearchPage):
                parse_data(html)

    def test_valid_row(self):
        self.assertEqual(parse_data(PAGE)[0]['lot_code'], '1')


class ParserTests(NetworkBlocked):
    def run_parser(self, responses):
        with patch.object(parser, 'warm_up'), patch.object(parser, 'fetch_page', side_effect=responses), patch.object(parser.time, 'sleep'), patch.object(parser, 'log') as log:
            result = parser.main()
        self.assertIn('summary', log.call_args.args[0])
        return result

    def test_complete(self):
        r = self.run_parser([PAGE, EMPTY, CARD])
        self.assertEqual((r.status, r.found, r.filtered, r.processed, r.load_errors), ('success', 1, 1, 1, 0))

    def test_empty_success(self):
        r = self.run_parser([EMPTY])
        self.assertEqual((r.status, r.found, r.lots), ('success', 0, []))

    def test_first_page_failure(self):
        r = self.run_parser([None])
        self.assertEqual((r.status, r.load_errors, r.failed_page), ('error', 1, 1))

    def test_later_page_failure_preserves_lots(self):
        r = self.run_parser([PAGE, None, CARD])
        self.assertEqual((r.status, r.found, r.processed, r.failed_page), ('partial', 1, 1, 2))
        self.assertEqual(r.load_errors, 1)

    def test_invalid_first_and_later_page(self):
        for responses, status in [(['bad'], 'error'), ([PAGE, 'bad', CARD], 'partial')]:
            with self.subTest(status=status):
                r = self.run_parser(responses)
                self.assertEqual(r.status, status)
                self.assertEqual(r.parse_errors, 1)

    def test_failed_card_preserves_lot(self):
        r = self.run_parser([PAGE, EMPTY, None])
        self.assertEqual((r.status, len(r.lots), r.processed, r.load_errors), ('partial', 1, 0, 1))

    def test_missing_date(self):
        r = self.run_parser([PAGE, EMPTY, '<html>no date</html>'])
        self.assertEqual((r.status, r.processed, r.parse_errors), ('partial', 0, 1))

    def test_unexpected_card_exception(self):
        r = self.run_parser([PAGE, EMPTY, RuntimeError('card failure')])
        self.assertEqual((r.status, r.processed, r.parse_errors), ('partial', 0, 1))

    def test_fetch_retries_unchanged(self):
        with patch.object(fetcher.session, 'get', side_effect=requests.ConnectTimeout('test')) as get, patch.object(fetcher.time, 'sleep') as sleep, patch.object(fetcher, 'log'):
            self.assertIsNone(fetcher.fetch_page('https://example.invalid'))
        self.assertEqual(get.call_count, 3)
        self.assertEqual([c.kwargs['timeout'] for c in get.call_args_list], [30, 30, 30])
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [3, 6, 9])


class BotTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        p = patch('socket.socket.connect', side_effect=AssertionError('Network forbidden'))
        p.start()
        self.addCleanup(p.stop)

    async def test_broadcast_continues_for_lots_and_users(self):
        result = parser.ParseResult(lots=[LOT, dict(LOT, lot_code='2')])
        with patch.object(app, 'run_parser_safe', new=AsyncMock(return_value=result)), patch.object(app.bot, 'send_message', new=AsyncMock(side_effect=[RuntimeError('failed'), None, None, None])) as send, patch.object(app, 'log') as log:
            await app.auto_parse()
        self.assertEqual([c.args[0] for c in send.call_args_list], [101, 101, 202, 202])
        self.assertIn('sent=3 failed=1', log.call_args.args[0])

    async def test_manual_continues_after_failure(self):
        result = parser.ParseResult(lots=[LOT, dict(LOT, lot_code='2')])
        message = SimpleNamespace(chat=SimpleNamespace(id=101), answer=AsyncMock(side_effect=[None, RuntimeError('failed'), None]))
        with patch.object(app, 'run_parser_safe', new=AsyncMock(return_value=result)), patch.object(app, 'log') as log:
            await app.parse_button(message)
        self.assertEqual(message.answer.await_count, 3)
        self.assertIn('sent=1 failed=1', log.call_args.args[0])

    async def test_error_skips_broadcast(self):
        with patch.object(app, 'run_parser_safe', new=AsyncMock(return_value=parser.ParseResult(status='error'))), patch.object(app.bot, 'send_message', new=AsyncMock()) as send:
            await app.auto_parse()
        send.assert_not_awaited()

    async def test_partial_warning_failure_does_not_stop_broadcast(self):
        result = parser.ParseResult(status='partial', lots=[LOT])
        with patch.object(app, 'run_parser_safe', new=AsyncMock(return_value=result)), patch.object(app.bot, 'send_message', new=AsyncMock(side_effect=[RuntimeError('warning failed'), None, None, None])) as send:
            await app.auto_parse()
        self.assertEqual(send.await_count, 4)
        self.assertEqual(send.call_args.args, (202, app.format_lot(LOT)))

    async def test_partial_empty_is_not_reported_as_no_active_lots(self):
        message = SimpleNamespace(chat=SimpleNamespace(id=101), answer=AsyncMock())
        with patch.object(app, 'run_parser_safe', new=AsyncMock(return_value=parser.ParseResult(status='partial'))):
            await app.parse_button(message)
        texts = [c.args[0] for c in message.answer.call_args_list]
        self.assertTrue(any('неполный' in t for t in texts))
        self.assertFalse(any('Нет активных' in t for t in texts))


if __name__ == '__main__':
    unittest.main()
