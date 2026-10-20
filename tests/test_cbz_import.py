import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from PIL import Image

from ballontranslator.utils.cbz import import_cbz
from ballontranslator.utils.proj_imgtrans import ProjImgTrans


class CBZImportTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.archive = Path(self.temp.name) / 'chapter.cbz'
        image = io.BytesIO()
        Image.new('RGB', (32, 32), 'white').save(image, 'PNG')
        self.image = image.getvalue()

    def write_archive(self, names):
        with zipfile.ZipFile(self.archive, 'w') as archive:
            for name in names:
                archive.writestr(name, self.image)

    def test_nested_pages_natural_order_and_project_reload_preserve_edits(self):
        self.write_archive(['chapter/10.png', 'chapter/2.png', 'chapter/1.png'])
        original = self.archive.read_bytes()
        folder = Path(import_cbz(str(self.archive)))
        pages = sorted(folder.glob('*.png'))
        self.assertEqual([p.name for p in pages], ['00001-1.png', '00002-2.png', '00003-10.png'])
        project = ProjImgTrans(str(folder))
        self.assertEqual(project.num_pages, 3)
        marker = folder / 'user-edit.txt'
        marker.write_text('keep')
        self.assertEqual(Path(import_cbz(str(self.archive))), folder)
        self.assertEqual(marker.read_text(), 'keep')
        self.assertEqual(self.archive.read_bytes(), original)

    def test_empty_archive_rejected_without_project_folder(self):
        self.write_archive(['ComicInfo.xml'])
        with self.assertRaisesRegex(ValueError, 'images'):
            import_cbz(str(self.archive))
        self.assertEqual(list(Path(self.temp.name).iterdir()), [self.archive])

    def test_unsafe_path_rejected(self):
        self.write_archive(['../escape.png'])
        with self.assertRaises(ValueError):
            import_cbz(str(self.archive))
        self.assertFalse((Path(self.temp.name).parent / 'escape.png').exists())

    def test_corrupt_image_does_not_leave_partial_project(self):
        with zipfile.ZipFile(self.archive, 'w') as archive:
            archive.writestr('1.png', b'broken')
        with self.assertRaises(Exception):
            import_cbz(str(self.archive))
        self.assertEqual(list(Path(self.temp.name).iterdir()), [self.archive])

    def test_changed_archive_creates_separate_project(self):
        self.write_archive(['1.png'])
        first = Path(import_cbz(str(self.archive)))
        self.write_archive(['1.png', '2.png'])
        second = Path(import_cbz(str(self.archive)))
        self.assertNotEqual(first, second)
        self.assertTrue((first / '00001-1.png').exists())

    def test_import_worker_emits_result(self):
        from ballontranslator.ui.io_thread import CBZImportThread
        self.write_archive(['1.png'])
        worker = CBZImportThread()
        results, failures = [], []
        worker.imported.connect(results.append)
        worker.failed.connect(failures.append)
        worker.archive_path = str(self.archive)
        worker.run()
        self.assertEqual(failures, [])
        self.assertEqual(len(results), 1)
        self.assertTrue(Path(results[0]).is_dir())

    def test_headless_open_loads_cbz_before_returning(self):
        from types import SimpleNamespace
        from unittest.mock import Mock, patch
        from ballontranslator.ui.mainwindow import MainWindow
        self.write_archive(['1.png'])
        opened = []
        window = SimpleNamespace(openDir=opened.append, cbz_import_thread=Mock())
        with patch('ballontranslator.ui.mainwindow.shared.HEADLESS', True), \
                patch('ballontranslator.ui.mainwindow.pcfg.let_textstyle_indep_flag', False):
            MainWindow.OpenProj(window, str(self.archive))
        self.assertEqual(len(opened), 1)
        self.assertEqual(ProjImgTrans(opened[0]).num_pages, 1)
        window.cbz_import_thread.start.assert_not_called()


if __name__ == '__main__':
    unittest.main()
