"""
Spanview frame class for PyGPSClient application.

This handles a frame containing a span of current satellite reception.

Created on 21 Apr 2021

:author: karri
:copyright: FFOY © 2021
:license: BSD 3-Clause
"""
# pylint: disable=invalid-name, too-many-instance-attributes, too-many-ancestors

from tkinter import Frame, Canvas, font, BOTH, YES
from .helpers import snr2col
from .globals import WIDGETU2, BGCOL, FGCOL, MAX_SNR, GNSS_LIST
import math

# Relative offsets of span axes and legend
AXIS_XL = 19
AXIS_XR = 10
AXIS_Y = 22
OL_WID = 2
LEG_XOFF = AXIS_XL + 20
LEG_YOFF = 5
LEG_GAP = 5
MAX_DB = 70


class SpanviewFrame(Frame):
    """
    Spanview frame class.
    """

    def __init__(self, app, *args, **kwargs):
        """
        Constructor.

        :param Frame app: reference to main tkinter application
        :param args: optional args to pass to Frame parent class
        :param kwargs: optional kwargs to pass to Frame parent class
        """

        self.__app = app  # Reference to main application class
        self.__master = self.__app.get_master()  # Reference to root class (Tk)

        Frame.__init__(self, self.__master, *args, **kwargs)

        def_w, def_h = WIDGETU2
        self.width = kwargs.get("width", def_w)
        self.height = kwargs.get("height", def_h)
        self._body()
        self.spoof = 0
        self.jamState = 0
        self.jamming = 0
        self.center = 0
        self.span = 0

        self.bind("<Configure>", self._on_resize)

    def _body(self):
        """
        Set up frame and widgets.
        """

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.can_spanview = Canvas(
            self, width=self.width, height=self.height, bg=BGCOL
        )
        self.can_spanview.pack(fill=BOTH, expand=YES)

    def init_span(self):
        """
        Initialise span view
        """

        w, h = self.width, self.height
        resize_font = font.Font(size=min(int(h / 25), 10))
        ticks = int(MAX_DB / 10)
        self.can_spanview.delete("all")
        ''' Y axis left '''
        self.can_spanview.create_line(AXIS_XL, 5, AXIS_XL, h - AXIS_Y, fill=FGCOL)
        ''' Y axis middle '''
        middlex = (w - AXIS_XR + 2 - AXIS_XL) / 2
        self.can_spanview.create_line(
            AXIS_XL + middlex, 5, AXIS_XL + middlex, h - AXIS_Y, fill=FGCOL, dash=(4,2)
        )

        ''' Y axis right '''
        self.can_spanview.create_line(
            w - AXIS_XR + 2, 5, w - AXIS_XR + 2, h - AXIS_Y, fill=FGCOL
        )
        for i in range(ticks, 0, -1):
            y = (h - AXIS_Y) * i / ticks
            ''' Horizontal grid lines '''
            self.can_spanview.create_line(AXIS_XL, y, w - AXIS_XR + 2, y, fill=FGCOL)
            ''' Y axis grid labels '''
            self.can_spanview.create_text(
                10,
                y,
                text=str(MAX_DB - (i * 10)),
                angle=90,
                fill=FGCOL,
                font=resize_font,
            )

        '''if self.__app.frm_settings.show_legend:
            self._draw_legend()
        '''

    def _draw_legend(self):
        """
        Draw GNSS color code legend
        """

        w = self.width / 9
        h = self.height / 15
        resize_font = font.Font(size=min(int(self.height / 25), 10))

        for i, (_, (gnssName, gnssCol)) in enumerate(GNSS_LIST.items()):
            x = LEG_XOFF + w * i
            self.can_spanview.create_rectangle(
                x,
                LEG_YOFF,
                x + w - LEG_GAP,
                LEG_YOFF + h,
                outline=gnssCol,
                fill=BGCOL,
                width=OL_WID,
            )
            self.can_spanview.create_text(
                (x + x + w - LEG_GAP) / 2,
                LEG_YOFF + h / 2,
                text=gnssName,
                fill=FGCOL,
                font=resize_font,
            )

    def _draw_jamming(self):
        """
        Draw jamming indicator info
        """

        w = self.width / 4
        h = self.height / 15
        resize_font = font.Font(size=min(int(self.height / 25), 10))

        x = LEG_XOFF + w * 0
        if self.spoof < 2:
            spoof_color = 'green'
        else:
            spoof_color = 'red'
        self.can_spanview.create_rectangle(
            x,
            LEG_YOFF,
            x + w - LEG_GAP,
            LEG_YOFF + h,
            outline=spoof_color,
            fill=BGCOL,
            width=OL_WID,
        )
        if self.spoof == 0:
            spooftext = 'deactivated'
        if self.spoof == 1:
            spooftext = 'no spoofing'
        if self.spoof == 2:
            spooftext = 'spoofing'
        if self.spoof == 3:
            spooftext = 'multiple spoof'
        self.can_spanview.create_text(
            (x + x + w - LEG_GAP) / 2,
            LEG_YOFF + h / 2,
            text=spooftext,
            fill=FGCOL,
            font=resize_font,
        )
        x = LEG_XOFF + w * 1
        jamstate_color = 'green'
        if self.jamState == 2:
            jamstate_color = 'yellow'
        if self.jamState == 3:
            jamstate_color = 'red'
        self.can_spanview.create_rectangle(
            x,
            LEG_YOFF,
            x + w - LEG_GAP,
            LEG_YOFF + h,
            outline=jamstate_color,
            fill=BGCOL,
            width=OL_WID,
        )
        jamstatetext = 'deactivated'
        if self.jamState == 1:
            jamstatetext = 'no jamming'
        if self.jamState == 2:
            jamstatetext = 'interference'
        if self.jamState == 3:
            jamstatetext = 'jammed'
        self.can_spanview.create_text(
            (x + x + w - LEG_GAP) / 2,
            LEG_YOFF + h / 2,
            text=jamstatetext,
            fill=FGCOL,
            font=resize_font,
        )
        x = LEG_XOFF + w * 2
        self.can_spanview.create_rectangle(
            x,
            LEG_YOFF,
            x + w - LEG_GAP,
            LEG_YOFF + h,
            outline='white',
            fill=BGCOL,
            width=OL_WID,
        )
        self.can_spanview.create_text(
            (x + x + w - LEG_GAP) / 2,
            LEG_YOFF + h / 2,
            text=str(self.jamming),
            fill=FGCOL,
            font=resize_font,
        )
        self.can_spanview.create_text(
            (x + w) / 2,
            14.6 * h,
            text=str(self.center / 1000000) + ' MHz span ' + str(self.span / 1000000) + ' MHz',
            fill=FGCOL,
            font=resize_font,
        )

    def update_spoof(self, spoof):
        self.spoof = spoof

    def update_jamming(self, jamState, jamming):
        self.jamState = jamState
        self.jamming = jamming

    def update_span(self, spectra, center, span):
        """
        Plot satellites' signal-to-noise ratio (cno).
        Automatically adjust y axis according to number of satellites in view.

        :param list data: array of satellite tuples (gnssId, svid, elev, azim, cno):
        :param int siv: number of satellites in view (default = 16)
        """

        w, h = self.width, self.height
        self.center = center
        self.span = span
        self.init_span()
        self._draw_jamming()

        offset = AXIS_XL + 2
        colwidth = (w - AXIS_XL - AXIS_XR + 1) / 16
        resize_font = font.Font(size=min(int(colwidth / 2), 10))
        polyline = []
        for x in range(256):
            polyline.append(offset + x * colwidth * 16 / 256)
            polyline.append(h - AXIS_Y - 1 - spectra[x] * (h - AXIS_Y - 1) / 256)
        self.can_spanview.create_line(polyline, fill='yellow')
        '''for d in sorted(data):  # sort by ascending gnssid, svid
            gnssId, prn, _, _, snr = d
            if snr in ("", "0", 0):
                snr = 1  # show 'place marker' in span
            else:
                snr = int(snr)
            snr_y = int(snr) * (h - AXIS_Y - 1) / MAX_SNR
            (_, ol_col) = GNSS_LIST[gnssId]
            prn = f"{int(prn):02}"
            self.can_spanview.create_rectangle(
                offset,
                h - AXIS_Y - 1,
                offset + colwidth - OL_WID,
                h - AXIS_Y - 1 - snr_y,
                outline=ol_col,
                fill=snr2col(snr),
                width=OL_WID,
            )
            self.can_spanview.create_text(
                offset + colwidth / 2,
                h - 10,
                text=prn,
                fill=FGCOL,
                font=resize_font,
                angle=35,
            )
            offset += colwidth
        '''

        self.can_spanview.update()

    def _on_resize(self, event):  # pylint: disable=unused-argument
        """
        Resize frame

        :param event event: resize event
        """

        self.width, self.height = self.get_size()

    def get_size(self):
        """
        Get current canvas size.

        :return: window size (width, height)
        :rtype: tuple
        """

        self.update_idletasks()  # Make sure we know about any resizing
        width = self.can_spanview.winfo_width()
        height = self.can_spanview.winfo_height()
        return (width, height)
