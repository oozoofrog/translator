#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import zipfile
import os
from pathlib import Path

class EPUBExtractor:
    def __init__(self, epub_path):
        self.epub_path = epub_path

    def extract(self, output_dir=None):
        if output_dir is None:
            output_dir = Path(self.epub_path).stem
        os.makedirs(output_dir, exist_ok=True)
        with zipfile.ZipFile(self.epub_path, 'r') as zip_file:
            zip_file.extractall(output_dir)
        print(f"✅ EPUB extracted to {output_dir}")
