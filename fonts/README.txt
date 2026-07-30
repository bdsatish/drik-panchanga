IndUni-H (Helvetica-compatible, Indology/IAST)
=============================================

``IndUni-H.ttc`` is a TrueType Collection of the four IndUni-H faces
(Regular, Bold, Oblique, BoldOblique) for ReportLab PDF embedding.

Source: https://bombay.indology.info/software/fonts/induni/
Upstream zip: IndUni-H.zip (OpenType/CFF on URW Nimbus Sans L).
License: GNU GPL v2 — https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
Upstream notes: ``README-H``.

ReportLab face indices in the collection:

  0  IndUni-H-Regular
  1  IndUni-H-Bold
  2  IndUni-H-Oblique
  3  IndUni-H-BoldOblique

Rebuild (maintainer; needs ``fonttools`` once):

  ./scripts/build_induni_ttc.sh

That script downloads IndUni-H.zip and converts faces with fontTools'
``Snippets/otf2ttf.py`` (fetched from GitHub; not kept in this repo).
