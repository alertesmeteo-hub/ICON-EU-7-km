import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
maps = importlib.import_module('icon_eu_maps')
ROOT = Path(__file__).resolve().parents[1]

class VectorMapsTests(unittest.TestCase):
    def test_vector_output_and_geographic_box(self):
        with tempfile.TemporaryDirectory() as tmp:
            for region in maps.REGIONS:
                west, east, south, north = maps.REGIONS[region][:4]
                lon = np.linspace(west, east, 40)
                lat = np.linspace(north, south, 35)
                xx, yy = np.meshgrid(lon, lat)
                rain = 160 * np.exp(-((xx - (west+east)/2)**2 + (yy-(south+north)/2)**2)/8)
                output = Path(tmp) / (region + '.png')
                box = maps._render(lon, lat, rain, 'precipitation', region, '2026092500', 120, output, ROOT/'config')
                self.assertTrue(output.exists())
                svg = ET.parse(output.with_suffix('.svg'))
                self.assertFalse(any(n.tag.endswith('}image') for n in svg.iter()), 'SVG must not embed a raster')
                self.assertGreater(sum(n.tag.endswith('}path') for n in svg.iter()), 50)
                self.assertTrue(all(0 < v < 1 for v in box))
                self.assertLessEqual(box[0] + box[2], 1)
                self.assertLessEqual(box[1] + box[3], 1)

    def test_wind_legend_steps(self):
        for key in ('vent', 'rafales'):
            np.testing.assert_array_equal(np.diff(maps.PRODUCTS[key]['levels']), 5)

    def test_probe_retains_native_points_and_maximum(self):
        lon = np.arange(2, 3, .0625)
        lat = np.arange(46, 45, -.0625)
        values = np.zeros((len(lat), len(lon)))
        values[3, 3] = 157
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)/'values.json'
            maps._write_probe_grid(lon, lat, values, 'france', target)
            grid = json.loads(target.read_text())
            self.assertEqual(len(grid['lons']), len(lon))
            self.assertEqual(len(grid['lats']), len(lat))
            self.assertEqual(grid['values'][3][3], 157)

if __name__ == '__main__':
    unittest.main()
