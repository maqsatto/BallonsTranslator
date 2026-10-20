import unittest
from unittest.mock import patch
import numpy as np
from ballontranslator.modules.ocr.ocr_ppv6_onnx import PaddleOCRv6ONNX
from ballontranslator.modules.ocr.utils.onnxocr import TextRecognizer


class PaddleCropWidthTest(unittest.TestCase):
    def test_gpu_preprocessing_preserves_right_end_of_wide_line(self):
        crop = np.full((48, 960, 3), 255, dtype=np.uint8)
        crop[:, 850:930] = 0
        ocr = PaddleOCRv6ONNX(device='cuda', rec_batch_num=1)
        with patch.object(ocr, '_ensure_cuda_dll_path'), \
                patch('onnxruntime.get_available_providers', return_value=['CUDAExecutionProvider']), \
                patch.object(TextRecognizer, 'get_onnx_session'), \
                patch.object(TextRecognizer, 'get_input_name'), \
                patch.object(TextRecognizer, 'get_output_name'):
            ocr._load_model()
        result = ocr.recognizer.resize_norm_img(crop, 20.0)
        self.assertEqual(result.shape, (3, 48, 960))
        self.assertTrue(np.all(result[:, :, 850:930] == -1.0))


if __name__ == '__main__':
    unittest.main()
