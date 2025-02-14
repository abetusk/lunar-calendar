import calendar
import datetime
import ephem # see http://rhodesmill.org/pyephem/
import math
import sys

import getopt
import random
import re

'''
Lunar Calendar Generator

This utility will generate an HTML Lunar Calendar for the year that you specify.
To run the utility, pass the year as a command-line argument - for example:

    python main.py 2018

When running the utility, the file 'template.html' must be present in the current
working directory.

Latest version of source code available from:
    https://github.com/codebox/lunar-calendar

Project home page:
   https://codebox.net/pages/lunar-calendar

This source code is released under the MIT Open Source License

© 2018 Rob Dawson
'''

LUNAR_CALENDAR_VERSION = "0.2.0"
DEFAULT_MOON_IMAGE = 'data/supermoon_l3_bw_s.png'

class Calendar:
    def __init__(self):
        self.html = open('template.html').read()
        self.moon_image = ""
        self.succinct_opt = False
        self.extra_opt = False
        self.footer_opt = False
        self.bg_color = ''

    def footer(self, opt=True):
        self.footer_opt = opt

    def succinct(self, opt=True):
        self.succinct_opt = opt

    def extra(self, opt=True):
        self.extra_opt = opt

    def backgroundColor(self, col):
        self.bg_color = col

    def _replace_in_html(self, key, value):
        self.html = self.html.replace('<!-- {} -->'.format(key), value)

    def _replace_in_html_wrapper(self, key, value):
        s = '(<!--|\/\*) {0}_BEG (-->|\*\/).*(<!--|\/\*) {0}_END (-->|\*\/)'.format(key)
        self.html = re.sub( s, value, self.html )

    def _calc_terminator_arc(self, lunation, disc_radius):
        right_of_centre = None
        lit_from_left = None
        L = None

        if lunation <= 0.25:
            L = lunation
            right_of_centre = True
            lit_from_left = False

        elif lunation <= 0.5:
            L = 0.5 - lunation
            right_of_centre = False
            lit_from_left = False

        elif lunation <= 0.75:
            L = lunation - 0.5
            right_of_centre = True
            lit_from_left = True

        else:
            L = 1 - lunation
            right_of_centre = False
            lit_from_left = True

        x = disc_radius * (1 - math.cos(2 * math.pi * L))
        n = disc_radius - x
        terminator_arc_radius = (disc_radius * disc_radius + n * n) / (2 * n)

        return terminator_arc_radius, right_of_centre, lit_from_left

    def _make_path(self, lunation, view_box_size):
        terminator_arc_radius, right_of_centre, lit_from_left = self._calc_terminator_arc(lunation, view_box_size/2)

        LIGHT_CSS_CLASS   = 'light'
        SHADOW_CSS_CLASS  = 'shadow'

        colour_left  = LIGHT_CSS_CLASS if lit_from_left else SHADOW_CSS_CLASS
        colour_right = SHADOW_CSS_CLASS if lit_from_left else LIGHT_CSS_CLASS

        move_to_top    = 'M{0},0'.format(view_box_size/2)
        disc_left_arc  = 'A {0} {0} 0 0 1 {0} 0'.format(view_box_size/2)
        disc_right_arc = 'A {0} {0} 0 0 0 {0} 0'.format(view_box_size/2)
        terminator_arc = 'A {0} {0} 0 0 {1} {2} {3}'.format(
            terminator_arc_radius, 1 if right_of_centre else 0, view_box_size/2, view_box_size)

        path_left  = '<path d="{0} {1} {2}" class="{3}"/>'.format(move_to_top, terminator_arc, disc_left_arc, colour_left)
        path_right = '<path d="{0} {1} {2}" class="{3}"/>'.format(move_to_top, terminator_arc, disc_right_arc, colour_right)

        return path_left + path_right

    def _make_path_mask(self, lunation, view_box_size, moon_opt):
        terminator_arc_radius, right_of_centre, lit_from_left = self._calc_terminator_arc(lunation, view_box_size/2)

        LIGHT_CSS_CLASS   = 'lightMask'
        SHADOW_CSS_CLASS  = 'shadowMask'

        colour_left  = LIGHT_CSS_CLASS if lit_from_left else SHADOW_CSS_CLASS
        colour_right = SHADOW_CSS_CLASS if lit_from_left else LIGHT_CSS_CLASS

        view_box_size = 1.0

        move_to_top    = 'M{0},0'.format(view_box_size/2.0)
        disc_left_arc  = 'A {0} {0} 0 0 1 {0} 0'.format(view_box_size/2.0)
        disc_right_arc = 'A {0} {0} 0 0 0 {0} 0'.format(view_box_size/2.0)
        terminator_arc = 'A {0} {0} 0 0 {1} {2} {3}'.format(
            terminator_arc_radius, 1 if right_of_centre else 0, view_box_size/2.0, view_box_size)

        path_left  = '<path d="{0} {1} {2}" class="{3}"/>'.format(move_to_top, terminator_arc, disc_left_arc, colour_left)
        path_right = '<path d="{0} {1} {2}" class="{3}"/>'.format(move_to_top, terminator_arc, disc_right_arc, colour_right)

        return path_left + path_right

    def _generate_moon(self, year, month, day):
        date = ephem.Date(datetime.date(year, month, day))

        preceding_new_moon = ephem.previous_new_moon(date)
        following_new_moon = ephem.next_new_moon(date)

        lunation = (date - preceding_new_moon) / (following_new_moon - preceding_new_moon)

        VIEW_BOX_SIZE = 100
        return '<svg width="100%" viewBox="0 0 {0} {0}">{1}</svg>'.format(VIEW_BOX_SIZE, self._make_path(lunation, VIEW_BOX_SIZE))

    def _generate_moon_image(self, year, month, day, moon_opt):
        date = ephem.Date(datetime.date(year, month, day))

        preceding_new_moon = ephem.previous_new_moon(date)
        following_new_moon = ephem.next_new_moon(date)

        lunation = (date - preceding_new_moon) / (following_new_moon - preceding_new_moon)

        mask_id = "mask_" + "".join(random.choices(['a', 'b', 'c', 'd', 'e', 'f', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'], k=20))
        overlay_id = "overlay_" + "".join(random.choices(['a', 'b', 'c', 'd', 'e', 'f', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'], k=20))


        overlay_svg = ''

        if self.extra_opt:
          if moon_opt["black"]:
              overlay_svg = "".join([
                '<svg viewBox="0 0 100 100">',
                '<defs>',
                '<radialGradient id="{0}">',
                '<stop offset="89%" stop-color="rgba(0,0,0,0.2)" />',
                '<stop offset="98%" stop-color="rgba(0,0,0,0.1)" />',
                '<stop offset="100%" stop-color="rgba(0,0,0,0.0)" />',
                '</radialGradient>',
                '</defs>',
                '<circle cx="46.5" cy="46.5" r="49" fill="url(#{0})"/>',
                '</svg>'
              ]).format(overlay_id)

          elif moon_opt["blue"]:
              overlay_svg = "".join([
                '<svg viewBox="0 0 100 100">',
                '<defs>',
                '<radialGradient id="{0}">',
                '<stop offset="89%" stop-color="rgba(0,0,255,0.15)" />',
                '<stop offset="98%" stop-color="rgba(0,0,128,0.05)" />',
                '<stop offset="100%" stop-color="rgba(0,0,0,0.0)" />',
                '</radialGradient>',
                '</defs>',
                '<circle cx="46.5" cy="46.5" r="49" fill="url(#{0})"/>',
                '</svg>'
              ]).format(overlay_id)

          elif moon_opt["full"]:
              overlay_svg = "".join([
                '<svg viewBox="0 0 100 100">',
                '<defs>',
                '<radialGradient id="{0}">',
                '<stop offset="89%" stop-color="rgba(255,255,255,0.5)" />',
                '<stop offset="96%" stop-color="rgba(128,128,128,0.05)" />',
                '<stop offset="100%" stop-color="rgba(64,64,64,0.00)" />',
                '</radialGradient>',
                '</defs>',
                '<circle cx="46.5" cy="46.5" r="49" fill="url(#{0})"/>',
                '</svg>'
              ]).format(overlay_id)

          elif moon_opt["new"]:
              overlay_svg = "".join([
                '<svg viewBox="0 0 100 100">',
                '<defs>',
                '<radialGradient id="{0}">',
                '<stop offset="89%" stop-color="rgba(0,0,0,0.15)" />',
                '<stop offset="96%" stop-color="rgba(0,0,0,0.05)" />',
                '<stop offset="100%" stop-color="rgba(0,0,0,0.00)" />',
                '</radialGradient>',
                '</defs>',
                '<circle cx="46.5" cy="46.5" r="49" fill="url(#{0})"/>',
                '</svg>'
              ]).format(overlay_id)


        VIEW_BOX_SIZE = 1
        svg_str = "".join([
          '<svg width="0" height="0">',
          '<mask id="{0}" maskUnits="objectBoundingBox" maskContentUnits="objectBoundingBox">{1}</mask>',
          '</svg>']).format(mask_id, self._make_path_mask(lunation, VIEW_BOX_SIZE, moon_opt))

        img_ele = "".join([
            '\n{0}',
            
            '<img src="{1}" width="93%" style="mask: url(#{2}); -webkit-mask: url(#{2});"></img>'
        ]).format(svg_str, self.moon_image, mask_id)


        return '\n{0} <div class="img-overlay-wrap"> <img src="{1}" width="93%" style="mask: url(#{2}); -webkit-mask: url(#{2});"></img> {3} </div>'.format(svg_str, self.moon_image, mask_id, overlay_svg)

    def _get_moon_dates(self, year, next_fn):
        start_of_year = ephem.Date(datetime.date(year, 1, 1))
        end_of_year   = ephem.Date(datetime.date(year + 1, 1, 1))

        moon_dates = []

        date = start_of_year
        previous_month = None
        while date < end_of_year:
            date = next_fn(date)
            date_and_time = date.datetime()

            formatted_date = date_and_time.strftime('%d %b %H:%M')
            second_in_month = date_and_time.month == previous_month

            yyyy_m_d = date_and_time.strftime("%Y/%-m/%-d")

            moon_dates.append((formatted_date, second_in_month, yyyy_m_d))
            previous_month = date_and_time.month

        return moon_dates[:-1]

    def _moon_key(self, m, d):
        return 'MOON_{:02d}_{:02d}'.format(m, d)

    def populate(self, year, moon_image=''):

        def build_markup(moon_dates, second_in_month_class):
            markup = []
            for moon_date in moon_dates:
                date, second_in_month, _ = moon_date
                markup.append('<span class="{}">{}</span>'.format(second_in_month_class if second_in_month else '', date))
            return markup

        new_moon_dates  = self._get_moon_dates(year, ephem.next_new_moon)
        full_moon_dates = self._get_moon_dates(year, ephem.next_full_moon)

        new_moon_map = {}
        full_moon_map = {}
        for md in new_moon_dates:
            dt, second_in_month, yyyy_m_d = md
            new_moon_map[yyyy_m_d] = second_in_month

        for md in full_moon_dates:
            dt, second_in_month, yyyy_m_d = md
            full_moon_map[yyyy_m_d] = second_in_month

        if len(moon_image) > 0:
            self.moon_image = moon_image

        for month in range(1, 13):
            _, days_in_month = calendar.monthrange(year, month)
            for day in range(1, days_in_month + 1):
                yyyy_m_d_str = str(year) + "/" + str(month) + "/" + str(day)

                moon_opt = {
                  "full": False,
                  "new": False,
                  "blue": False,
                  "black": False
                }

                if yyyy_m_d_str in new_moon_map:
                    moon_opt["new"] = True
                    moon_opt["black"] = new_moon_map[yyyy_m_d_str]

                if yyyy_m_d_str in full_moon_map:
                    moon_opt["full"] = True
                    moon_opt["blue"] = full_moon_map[yyyy_m_d_str]

                key = self._moon_key(month, day)
                if len(moon_image) > 0:
                  moon = self._generate_moon_image(year, month, day, moon_opt)
                else:
                  moon = self._generate_moon(year, month, day)
                self._replace_in_html(key, moon)

        self._replace_in_html('YEAR', str(year))

        new_moon_markup  = build_markup(new_moon_dates,  'blackMoon')
        full_moon_markup = build_markup(full_moon_dates, 'blueMoon')

        if self.succinct_opt:
            self._replace_in_html_wrapper('NEW_MOONS_WRAPPER',  '')
            self._replace_in_html_wrapper('FULL_MOONS_WRAPPER', '')
            self._replace_in_html_wrapper('FOOTER_WRAPPER', '')
        else:
            self._replace_in_html('NEW_MOONS',  ''.join(new_moon_markup))
            self._replace_in_html('FULL_MOONS', ''.join(full_moon_markup))

        if len(self.bg_color) > 0:
            self._replace_in_html_wrapper('BG_COLOR_WRAPPER', "background-color: {0};".format(self.bg_color))

        if not self.footer_opt:
            self._replace_in_html_wrapper('FOOTER_WRAPPER', '')
            


    def save(self, path):
        open(path, 'w').write(self.html)

old = False
if old:
  if __name__ == '__main__':
      year = None
      try:
          year = int(sys.argv[1])
      except:
          print('Error, please specify a year: python {} <year>'.format(sys.argv[0]))
          sys.exit(1)
      
      cal = Calendar()
      cal.populate(year)
      output_file = 'lunar_calendar_{}.html'.format(year)
      cal.save(output_file)
      
      print('Success! Calendar saved to file {}'.format(output_file))

def version(io):
    io.write("Version: " + LUNAR_CALENDAR_VERSION + "\n")

def usage(io):
    io.write("Lunar Calendar generator\n")
    version(io)
    io.write("\n")
    io.write("usage:\n")
    io.write("\n")
    io.write("  python3 main.py [-h] [-v] [-y year] [-E] [-M] [-S] [-F] [-o output_file] [-i moon_image] [year]\n")
    io.write("\n")
    io.write("    -y year         Year to generate\n")
    io.write("    -o output_file  Output HTML (default 'lunar_calendar_YEAR.html')\n")
    io.write("    -M              Use moon image\n")
    io.write("    -E              Enhance new, full, black and blue moon images with colors (image only)\n")
    io.write("    -S              Succinct (remove footer and new/full moon dates)\n")
    io.write("    -F              Remove only the footer\n")
    io.write("    -i moon_image   Moon image to use ('{0}')\n".format(DEFAULT_MOON_IMAGE))
    io.write("    -h              Help (this screen)\n")
    io.write("    -v              Print version\n")
    io.write("\n")


def main():
    #moon_img = 'data/supermoon_l3_bw.png'
    moon_img = DEFAULT_MOON_IMAGE
    output_file = ''
    year = None

    moon_img_opt = False
    succinct_opt = False
    extra_opt = False
    footer_opt = True

    bg_color = ''

    try:
      opts, args = getopt.getopt(sys.argv[1:], "hvo:y:Mi:SEFc:", ["help", "version", "year=", "output=", "image=", "moon", "succinct", "extra", "no-footer", "color"])
    except getopt.GetoptError as err:
        sys.stderr.write(str(err) + "\n")
        usage(sys.stderr)
        sys.exit(2)

    for opt,arg in opts:
        if opt in ["-h", "--help"]:
            usage(sys.stdout)
            sys.exit(0)
        elif opt in ["-v", "--version"]:
            version(sys.stdout)
            sys.exit(0)
        elif opt in ["-o", "--output"]:
            output_file = arg
        elif opt in ["-y", "--year"]:
            year = arg
        elif opt in ["-M", "--moon"]:
            moon_img_opt = True
        elif opt in ["-i", "--image"]:
            moon_img = arg
            moon_img_opt = True
        elif opt in ["-S", "--succinct"]:
            succinct_opt = True
        elif opt in ["-E", "--extra"]:
            extra_opt = True
        elif opt in ["-F", "--no-footer"]:
            footer_opt = False
        elif opt in ["-c", "--color"]:
            bg_color = arg
        else:
            sys.stderr.write("Unknown option: " + opt)
            usage(sys.stdout)
            sys.exit(2)

    if len(args) > 0:
        year = args[0]

    if len(output_file) == 0:
        output_file = 'lunar_calendar_{}.html'.format(year)

    if year is None:
        sys.stderr.write('\nError, please specify a year: python {} <year>\n\n'.format(sys.argv[0]))
        usage(sys.stderr)
        sys.exit(1)

    try:
        year = int(year)
    except:
        sys.stderr.write('\nError, please specify a year: python {} <year>\n\n'.format(sys.argv[0]))
        usage(sys.stderr)
        sys.exit(1)
    
    cal = Calendar()

    if succinct_opt: cal.succinct(succinct_opt)
    if extra_opt: cal.extra(extra_opt)
    cal.footer(footer_opt)
    if len(bg_color) > 0: cal.backgroundColor(bg_color)

    if moon_img_opt:
        cal.populate(year, moon_img)
    else:
        cal.populate(year)
    cal.save(output_file)
    
    print('Success! Calendar saved to file {}'.format(output_file))


if __name__ == "__main__":
    main()
    sys.exit(0)
