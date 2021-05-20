"""
UBX Protocol handler

Uses pyubx2 library for parsing

Created on 30 Sep 2020

:author: semuadmin
:copyright: SEMU Consulting © 2020
:license: BSD 3-Clause
"""
# pylint: disable=invalid-name

from datetime import datetime
from pyubx2 import UBXMessage, UBXReader, UBX_MSGIDS, VALCKSUM
from pyubx2.ubxhelpers import itow2utc, gpsfix2str
from .globals import GLONASS_NMEA
from .helpers import svid2gnssid

BOTH = 3
UBX = 1
NMEA = 2


class UBXHandler:
    """
    UBXHandler class
    """

    def __init__(self, app):
        """
        Constructor.

        :param Frame app: reference to main tkinter application
        """

        self.__app = app  # Reference to main application class
        self.__master = self.__app.get_master()  # Reference to root class (Tk)

        self._raw_data = None
        self._parsed_data = None
        self.gsv_data = (
            []
        )  # Holds array of current satellites in view from NMEA GSV or UBX NAV-SVINFO sentences
        self.lon = 0
        self.lat = 0
        self.alt = 0
        self.track = 0
        self.speed = 0
        self.pdop = 0
        self.hdop = 0
        self.vdop = 0
        self.hacc = 0
        self.vacc = 0
        self.utc = ""
        self.sip = 0
        self.fix = "-"

    def process_data(self, data: bytes) -> UBXMessage:
        """
        Process UBX message type

        :param bytes data: raw data
        :return: UBXMessage
        :rtype: UBXMessage
        """

        if data is None:
            return None

        parsed_data = UBXReader.parse(data, validate=VALCKSUM)

        if parsed_data.identity == "ACK-ACK":
            self._process_ACK_ACK(parsed_data)
        if parsed_data.identity == "ACK-NAK":
            self._process_ACK_NAK(parsed_data)
        if parsed_data.identity == "CFG-MSG":
            self._process_CFG_MSG(parsed_data)
        if parsed_data.identity == "CFG-PRT":
            self._process_CFG_PRT(parsed_data)
        if parsed_data.identity == "CFG-RATE":
            self._process_CFG_RATE(parsed_data)
        if parsed_data.identity == "CFG-INF":
            self._process_CFG_INF(parsed_data)
        if parsed_data.identity == "CFG-VALGET":
            self._process_CFG_VALGET(parsed_data)
        if parsed_data.identity == "NAV-POSLLH":
            self._process_NAV_POSLLH(parsed_data)
        if parsed_data.identity == "NAV-PVT":
            self._process_NAV_PVT(parsed_data)
        if parsed_data.identity == "NAV-VELNED":
            self._process_NAV_VELNED(parsed_data)
        if parsed_data.identity == "NAV-SAT":
            self._process_NAV_SAT(parsed_data)
        if parsed_data.identity == "NAV-SVINFO":
            self._process_NAV_SVINFO(parsed_data)
        if parsed_data.identity == "NAV-SOL":
            self._process_NAV_SOL(parsed_data)
        if parsed_data.identity == "NAV-DOP":
            self._process_NAV_DOP(parsed_data)
        if parsed_data.identity == "HNR-PVT":
            self._process_HNR_PVT(parsed_data)
        if parsed_data.identity == "MON-VER":
            self._process_MON_VER(parsed_data)
        if parsed_data.identity == "MON-HW":
            self._process_MON_HW(parsed_data)
        if parsed_data.identity == "NAV-STATUS":
            self._process_NAV_STATUS(parsed_data)
        if parsed_data.identity == "MON-RF":
            self._process_MON_RF(parsed_data)
        if parsed_data.identity == "MON-SPAN":
            self._process_MON_SPAN(parsed_data)
        if data or parsed_data:
            self._update_console(data, parsed_data)

        return parsed_data

    def _update_console(self, raw_data: bytes, parsed_data: UBXMessage):
        """
        Write the incoming data to the console in raw or parsed format.

        :param bytes raw_data: raw data
        :param UBXMessage parsed_data: UBXMessage
        """

        if self.__app.frm_settings.raw:
            self.__app.frm_console.update_console(str(raw_data))
        else:
            self.__app.frm_console.update_console(str(parsed_data))

    def _process_ACK_ACK(self, data: UBXMessage):
        """
        Process CFG-MSG sentence - UBX message configuration.

        :param UBXMessage data: ACK_ACK parsed message
        """

        (ubxClass, ubxID) = UBXMessage.msgclass2bytes(data.clsID, data.msgID)

        # update the UBX config panel
        if self.__app.dlg_ubxconfig is not None:
            self.__app.dlg_ubxconfig.update_pending(
                "ACK-ACK", msgtype=UBX_MSGIDS[ubxClass + ubxID]
            )

    def _process_ACK_NAK(self, data: UBXMessage):
        """
        Process CFG-MSG sentence - UBX message configuration.

        :param UBXMessage data: ACK_NAK parsed message
        """

        (ubxClass, ubxID) = UBXMessage.msgclass2bytes(data.clsID, data.msgID)

        # update the UBX config panel
        if self.__app.dlg_ubxconfig is not None:
            self.__app.dlg_ubxconfig.update_pending(
                "ACK-NAK", msgtype=UBX_MSGIDS[ubxClass + ubxID]
            )

    def _process_CFG_MSG(self, data: UBXMessage):
        """
        Process CFG-MSG sentence - UBX message configuration.

        :param UBXMessage data: CFG-MSG parsed message
        """

        (ubxClass, ubxID) = UBXMessage.msgclass2bytes(data.msgClass, data.msgID)

        ddcrate = data.rateDDC
        uart1rate = data.rateUART1
        uart2rate = data.rateUART2
        usbrate = data.rateUSB
        spirate = data.rateSPI

        # update the UBX config panel
        if self.__app.dlg_ubxconfig is not None:
            self.__app.dlg_ubxconfig.update_pending(
                "CFG-MSG",
                msgtype=UBX_MSGIDS[ubxClass + ubxID],
                ddcrate=ddcrate,
                uart1rate=uart1rate,
                uart2rate=uart2rate,
                usbrate=usbrate,
                spirate=spirate,
            )

    def _process_CFG_INF(self, data: UBXMessage):  # pylint: disable=unused-argument
        """
        Process CFG-INF sentence - UBX info message configuration.

        :param UBXMessage data: CFG-INF parsed message
        """

        # update the UBX config panel
        if self.__app.dlg_ubxconfig is not None:
            self.__app.dlg_ubxconfig.update_pending("CFG-INF")

    def _process_CFG_PRT(self, data: UBXMessage):
        """
        Process CFG-PRT sentence - UBX port configuration.

        :param UBXMessage data: CFG-PRT parsed message
        """

        # update the UBX config panel
        if self.__app.dlg_ubxconfig is not None:
            self.__app.dlg_ubxconfig.update_pending(
                "CFG-PRT",
                portid=data.portID,
                bpsrate=data.baudRate,
                inprot=data.inProtoMask,
                outprot=data.outProtoMask,
            )

    def _process_CFG_RATE(self, data: UBXMessage):
        """
        Process CFG-RATE sentence - UBX solution rate configuration.

        :param UBXMessage data: CFG-RATE parsed message
        """

        # update the UBX config panel
        if self.__app.dlg_ubxconfig is not None:
            self.__app.dlg_ubxconfig.update_pending(
                "CFG-RATE",
                measrate=data.measRate,
                navrate=data.navRate,
                timeref=data.timeRef,
            )

    def _process_CFG_VALGET(self, data: UBXMessage):  # pylint: disable=unused-argument
        """
        Process CFG-VALGET sentence.

        :param UBXMessage data: CFG-VALGET parsed message
        """

        # update the UBX config panel
        if self.__app.dlg_ubxconfig is not None:
            self.__app.dlg_ubxconfig.update_pending(
                "CFG-VALGET",
                data=data,
            )

    def _process_NAV_POSLLH(self, data: UBXMessage):
        """
        Process NAV-LLH sentence - Latitude, Longitude, Height.

        :param UBXMessage data: NAV-POSLLH parsed message
        """

        try:
            self.utc = itow2utc(data.iTOW)
            self.lat = data.lat / 10 ** 7
            self.lon = data.lon / 10 ** 7
            self.alt = data.hMSL / 1000
            self.hacc = data.hAcc / 1000
            self.vacc = data.vAcc / 1000
            self.__app.frm_banner.update_banner(
                time=self.utc,
                lat=self.lat,
                lon=self.lon,
                alt=self.alt,
                hacc=self.hacc,
                vacc=self.vacc,
            )

            self.__app.frm_mapview.update_map(self.lat, self.lon, self.hacc)

        except ValueError:
            # self.__app.set_status(ube.UBXMessageError(err), "red")
            pass

    def _process_NAV_PVT(self, data: UBXMessage):
        """
        Process NAV-PVT sentence -  Navigation position velocity time solution.

        :param UBXMessage data: NAV-PVT parsed message
        """

        try:
            self.utc = itow2utc(data.iTOW)
            self.lat = data.lat / 10 ** 7
            self.lon = data.lon / 10 ** 7
            self.alt = data.hMSL / 1000
            self.hacc = data.hAcc / 1000
            self.vacc = data.vAcc / 1000
            self.pdop = data.pDOP / 100
            self.sip = data.numSV
            self.speed = data.gSpeed / 1000  # m/s
            self.track = data.headMot / 10 ** 5
            fix = gpsfix2str(data.fixType)
            self.__app.frm_banner.update_banner(
                time=self.utc,
                lat=self.lat,
                lon=self.lon,
                alt=self.alt,
                hacc=self.hacc,
                vacc=self.vacc,
                dop=self.pdop,
                sip=self.sip,
                speed=self.speed,
                fix=fix,
                track=self.track,
            )

            self.__app.frm_mapview.update_map(self.lat, self.lon, self.hacc, fix=fix)

            if (
                self.__app.frm_settings.record_track
                and self.lat != ""
                and self.lon != ""
            ):
                time = (
                    datetime(
                        data.year,
                        data.month,
                        data.day,
                        data.hour,
                        data.min,
                        data.second,
                    ).isoformat()
                    + "Z"
                )
                if fix == "3D":
                    fix = "3d"
                elif fix == "2D":
                    fix = "2d"
                else:
                    fix = "none"
                self.__app.file_handler.add_trackpoint(
                    self.lat,
                    self.lon,
                    ele=self.alt,
                    time=time,
                    fix=fix,
                    sat=self.sip,
                    pdop=self.pdop,
                )
        except ValueError:
            # self.__app.set_status(ube.UBXMessageError(err), "red")
            pass

    def _process_NAV_STATUS(self, data: UBXMessage):
        # spoofing indicator in flags(2)
        spoof = data.flags2[0] // 8
        # 0 = deactivated
        # 1 = no spoofing indicated
        # 2 = spoofing indicated
        # 3 = multiple spoofing indications
        self.__app.frm_spanview.update_spoof(spoof)

    def _process_NAV_VELNED(self, data: UBXMessage):
        """
        Process NAV-VELNED sentence - Velocity Solution in North East Down format.

        :param UBXMessage data: NAV-VELNED parsed message
        """

        try:
            self.track = data.heading / 10 ** 5
            self.speed = data.gSpeed / 100  # m/s
            self.__app.frm_banner.update_banner(speed=self.speed, track=self.track)
        except ValueError:
            # self.__app.set_status(ube.UBXMessageError(err), "red")
            pass

    def _process_NAV_SAT(self, data: UBXMessage):
        """
        Process NAV-SAT sentences - Space Vehicle Information.

        NB: For consistency with NMEA GSV and UBX NAV-SVINFO message types,
        this uses the NMEA SVID numbering range for GLONASS satellites
        (65 - 96) rather than the Slot ID (1-24) by default.
        To change this, set the GLONASS_NMEA flag in globals.py to False.

        :param UBXMessage data: NAV-SAT parsed message
        """

        try:
            self.gsv_data = []
            num_siv = int(data.numCh)

            for i in range(num_siv):
                idx = "_{0:0=2d}".format(i + 1)
                gnssId = getattr(data, "gnssId" + idx)
                svid = getattr(data, "svId" + idx)
                # use NMEA GLONASS numbering (65-96) rather than slotID (1-24)
                if gnssId == 6 and svid < 25 and svid != 255 and GLONASS_NMEA:
                    svid += 64
                elev = getattr(data, "elev" + idx)
                azim = getattr(data, "azim" + idx)
                cno = getattr(data, "cno" + idx)
                if (
                    cno == 0 and not self.__app.frm_settings.show_zero
                ):  # omit sats with zero signal
                    continue
                self.gsv_data.append((gnssId, svid, elev, azim, cno))
            self.__app.frm_banner.update_banner(siv=len(self.gsv_data))
            self.__app.frm_satview.update_sats(self.gsv_data)
            self.__app.frm_graphview.update_graph(self.gsv_data, len(self.gsv_data))
        except ValueError:
            # self.__app.set_status(ube.UBXMessageError(err), "red")
            pass

    def _process_NAV_SVINFO(self, data: UBXMessage):
        """
        Process NAV-SVINFO sentences - Space Vehicle Information.

        NB: Since UBX Gen8 this message is deprecated in favour of NAV-SAT

        :param UBXMessage data: NAV-SVINFO parsed message
        """

        try:
            self.gsv_data = []
            num_siv = int(data.numCh)

            for i in range(num_siv):
                idx = "_{0:0=2d}".format(i + 1)
                svid = getattr(data, "svid" + idx)
                gnssId = svid2gnssid(svid)  # derive gnssId from svid
                elev = getattr(data, "elev" + idx)
                azim = getattr(data, "azim" + idx)
                cno = getattr(data, "cno" + idx)
                if (
                    cno == 0 and not self.__app.frm_settings.show_zero
                ):  # omit sats with zero signal
                    continue
                self.gsv_data.append((gnssId, svid, elev, azim, cno))
            self.__app.frm_banner.update_banner(siv=len(self.gsv_data))
            self.__app.frm_satview.update_sats(self.gsv_data)
            self.__app.frm_graphview.update_graph(self.gsv_data, len(self.gsv_data))
        except ValueError:
            # self.__app.set_status(ube.UBXMessageError(err), "red")
            pass

    def _process_NAV_SOL(self, data: UBXMessage):
        """
        Process NAV-SOL sentence - Navigation Solution.

        :param UBXMessage data: NAV-SOL parsed message
        """

        try:
            self.pdop = data.pDOP / 100
            self.sip = data.numSV
            fix = gpsfix2str(data.gpsFix)

            self.__app.frm_banner.update_banner(dop=self.pdop, fix=fix, sip=self.sip)
        except ValueError:
            # self.__app.set_status(ube.UBXMessageError(err), "red")
            pass

    def _process_NAV_DOP(self, data: UBXMessage):
        """
        Process NAV-DOP sentence - Dilution of Precision.

        :param UBXMessage data: NAV-DOP parsed message
        """

        try:
            self.pdop = data.pDOP / 100
            self.hdop = data.hDOP / 100
            self.vdop = data.vDOP / 100

            self.__app.frm_banner.update_banner(
                dop=self.pdop, hdop=self.hdop, vdop=self.vdop
            )
        except ValueError:
            # self.__app.set_status(ube.UBXMessageError(err), "red")
            pass

    def _process_HNR_PVT(self, data: UBXMessage):
        """
        Process HNR-PVT sentence -  High Rate Navigation position velocity time solution.

        :param UBXMessage data: HNR-PVT parsed message
        """

        try:
            self.utc = itow2utc(data.iTOW)
            self.lat = data.lat / 10 ** 7
            self.lon = data.lon / 10 ** 7
            self.alt = data.hMSL / 1000
            self.hacc = data.hAcc / 1000
            self.vacc = data.vAcc / 1000
            self.speed = data.gSpeed / 1000  # m/s
            self.track = data.headMot / 10 ** 5
            fix = gpsfix2str(data.gpsFix)
            self.__app.frm_banner.update_banner(
                time=self.utc,
                lat=self.lat,
                lon=self.lon,
                alt=self.alt,
                hacc=self.hacc,
                vacc=self.vacc,
                speed=self.speed,
                fix=fix,
                track=self.track,
            )

            self.__app.frm_mapview.update_map(self.lat, self.lon, self.hacc, fix=fix)

            if (
                self.__app.frm_settings.record_track
                and self.lat != ""
                and self.lon != ""
            ):
                time = (
                    datetime(
                        data.year,
                        data.month,
                        data.day,
                        data.hour,
                        data.min,
                        data.second,
                    ).isoformat()
                    + "Z"
                )
                if fix == "3D":
                    fix = "3d"
                elif fix == "2D":
                    fix = "2d"
                else:
                    fix = "none"
                self.__app.file_handler.add_trackpoint(
                    self.lat,
                    self.lon,
                    ele=self.alt,
                    time=time,
                    fix=fix,
                )
        except ValueError:
            # self.__app.set_status(ube.UBXMessageError(err), "red")
            pass

    def _process_MON_RF(self, data: UBXMessage):
        # jamming indicators
        self.__app.frm_spanview.update_jamming(data.flags_01[0], data.jamInd_01)

    def _process_MON_SPAN(self, data: UBXMessage):
        # spectrum display
        spectra = []
        spectra.append(data.spectrum_01_01)
        spectra.append(data.spectrum_01_02)
        spectra.append(data.spectrum_01_03)
        spectra.append(data.spectrum_01_04)
        spectra.append(data.spectrum_01_05)
        spectra.append(data.spectrum_01_06)
        spectra.append(data.spectrum_01_07)
        spectra.append(data.spectrum_01_08)
        spectra.append(data.spectrum_01_09)
        spectra.append(data.spectrum_01_10)
        spectra.append(data.spectrum_01_11)
        spectra.append(data.spectrum_01_12)
        spectra.append(data.spectrum_01_13)
        spectra.append(data.spectrum_01_14)
        spectra.append(data.spectrum_01_15)
        spectra.append(data.spectrum_01_16)
        spectra.append(data.spectrum_01_17)
        spectra.append(data.spectrum_01_18)
        spectra.append(data.spectrum_01_19)
        spectra.append(data.spectrum_01_20)
        spectra.append(data.spectrum_01_21)
        spectra.append(data.spectrum_01_22)
        spectra.append(data.spectrum_01_23)
        spectra.append(data.spectrum_01_24)
        spectra.append(data.spectrum_01_25)
        spectra.append(data.spectrum_01_26)
        spectra.append(data.spectrum_01_27)
        spectra.append(data.spectrum_01_28)
        spectra.append(data.spectrum_01_29)
        spectra.append(data.spectrum_01_30)
        spectra.append(data.spectrum_01_31)
        spectra.append(data.spectrum_01_32)
        spectra.append(data.spectrum_01_33)
        spectra.append(data.spectrum_01_34)
        spectra.append(data.spectrum_01_35)
        spectra.append(data.spectrum_01_36)
        spectra.append(data.spectrum_01_37)
        spectra.append(data.spectrum_01_38)
        spectra.append(data.spectrum_01_39)
        spectra.append(data.spectrum_01_40)
        spectra.append(data.spectrum_01_41)
        spectra.append(data.spectrum_01_42)
        spectra.append(data.spectrum_01_43)
        spectra.append(data.spectrum_01_44)
        spectra.append(data.spectrum_01_45)
        spectra.append(data.spectrum_01_46)
        spectra.append(data.spectrum_01_47)
        spectra.append(data.spectrum_01_48)
        spectra.append(data.spectrum_01_49)
        spectra.append(data.spectrum_01_50)
        spectra.append(data.spectrum_01_51)
        spectra.append(data.spectrum_01_52)
        spectra.append(data.spectrum_01_53)
        spectra.append(data.spectrum_01_54)
        spectra.append(data.spectrum_01_55)
        spectra.append(data.spectrum_01_56)
        spectra.append(data.spectrum_01_57)
        spectra.append(data.spectrum_01_58)
        spectra.append(data.spectrum_01_59)
        spectra.append(data.spectrum_01_60)
        spectra.append(data.spectrum_01_61)
        spectra.append(data.spectrum_01_62)
        spectra.append(data.spectrum_01_63)
        spectra.append(data.spectrum_01_64)
        spectra.append(data.spectrum_01_65)
        spectra.append(data.spectrum_01_66)
        spectra.append(data.spectrum_01_67)
        spectra.append(data.spectrum_01_68)
        spectra.append(data.spectrum_01_69)
        spectra.append(data.spectrum_01_70)
        spectra.append(data.spectrum_01_71)
        spectra.append(data.spectrum_01_72)
        spectra.append(data.spectrum_01_73)
        spectra.append(data.spectrum_01_74)
        spectra.append(data.spectrum_01_75)
        spectra.append(data.spectrum_01_76)
        spectra.append(data.spectrum_01_77)
        spectra.append(data.spectrum_01_78)
        spectra.append(data.spectrum_01_79)
        spectra.append(data.spectrum_01_80)
        spectra.append(data.spectrum_01_81)
        spectra.append(data.spectrum_01_82)
        spectra.append(data.spectrum_01_83)
        spectra.append(data.spectrum_01_84)
        spectra.append(data.spectrum_01_85)
        spectra.append(data.spectrum_01_86)
        spectra.append(data.spectrum_01_87)
        spectra.append(data.spectrum_01_88)
        spectra.append(data.spectrum_01_89)
        spectra.append(data.spectrum_01_90)
        spectra.append(data.spectrum_01_91)
        spectra.append(data.spectrum_01_92)
        spectra.append(data.spectrum_01_93)
        spectra.append(data.spectrum_01_94)
        spectra.append(data.spectrum_01_95)
        spectra.append(data.spectrum_01_96)
        spectra.append(data.spectrum_01_97)
        spectra.append(data.spectrum_01_98)
        spectra.append(data.spectrum_01_99)
        spectra.append(data.spectrum_01_100)
        spectra.append(data.spectrum_01_101)
        spectra.append(data.spectrum_01_102)
        spectra.append(data.spectrum_01_103)
        spectra.append(data.spectrum_01_104)
        spectra.append(data.spectrum_01_105)
        spectra.append(data.spectrum_01_106)
        spectra.append(data.spectrum_01_107)
        spectra.append(data.spectrum_01_108)
        spectra.append(data.spectrum_01_109)
        spectra.append(data.spectrum_01_110)
        spectra.append(data.spectrum_01_111)
        spectra.append(data.spectrum_01_112)
        spectra.append(data.spectrum_01_113)
        spectra.append(data.spectrum_01_114)
        spectra.append(data.spectrum_01_115)
        spectra.append(data.spectrum_01_116)
        spectra.append(data.spectrum_01_117)
        spectra.append(data.spectrum_01_118)
        spectra.append(data.spectrum_01_119)
        spectra.append(data.spectrum_01_120)
        spectra.append(data.spectrum_01_121)
        spectra.append(data.spectrum_01_122)
        spectra.append(data.spectrum_01_123)
        spectra.append(data.spectrum_01_124)
        spectra.append(data.spectrum_01_125)
        spectra.append(data.spectrum_01_126)
        spectra.append(data.spectrum_01_127)
        spectra.append(data.spectrum_01_128)
        spectra.append(data.spectrum_01_129)
        spectra.append(data.spectrum_01_130)
        spectra.append(data.spectrum_01_131)
        spectra.append(data.spectrum_01_132)
        spectra.append(data.spectrum_01_133)
        spectra.append(data.spectrum_01_134)
        spectra.append(data.spectrum_01_135)
        spectra.append(data.spectrum_01_136)
        spectra.append(data.spectrum_01_137)
        spectra.append(data.spectrum_01_138)
        spectra.append(data.spectrum_01_139)
        spectra.append(data.spectrum_01_140)
        spectra.append(data.spectrum_01_141)
        spectra.append(data.spectrum_01_142)
        spectra.append(data.spectrum_01_143)
        spectra.append(data.spectrum_01_144)
        spectra.append(data.spectrum_01_145)
        spectra.append(data.spectrum_01_146)
        spectra.append(data.spectrum_01_147)
        spectra.append(data.spectrum_01_148)
        spectra.append(data.spectrum_01_149)
        spectra.append(data.spectrum_01_150)
        spectra.append(data.spectrum_01_151)
        spectra.append(data.spectrum_01_152)
        spectra.append(data.spectrum_01_153)
        spectra.append(data.spectrum_01_154)
        spectra.append(data.spectrum_01_155)
        spectra.append(data.spectrum_01_156)
        spectra.append(data.spectrum_01_157)
        spectra.append(data.spectrum_01_158)
        spectra.append(data.spectrum_01_159)
        spectra.append(data.spectrum_01_160)
        spectra.append(data.spectrum_01_161)
        spectra.append(data.spectrum_01_162)
        spectra.append(data.spectrum_01_163)
        spectra.append(data.spectrum_01_164)
        spectra.append(data.spectrum_01_165)
        spectra.append(data.spectrum_01_166)
        spectra.append(data.spectrum_01_167)
        spectra.append(data.spectrum_01_168)
        spectra.append(data.spectrum_01_169)
        spectra.append(data.spectrum_01_170)
        spectra.append(data.spectrum_01_171)
        spectra.append(data.spectrum_01_172)
        spectra.append(data.spectrum_01_173)
        spectra.append(data.spectrum_01_174)
        spectra.append(data.spectrum_01_175)
        spectra.append(data.spectrum_01_176)
        spectra.append(data.spectrum_01_177)
        spectra.append(data.spectrum_01_178)
        spectra.append(data.spectrum_01_179)
        spectra.append(data.spectrum_01_180)
        spectra.append(data.spectrum_01_181)
        spectra.append(data.spectrum_01_182)
        spectra.append(data.spectrum_01_183)
        spectra.append(data.spectrum_01_184)
        spectra.append(data.spectrum_01_185)
        spectra.append(data.spectrum_01_186)
        spectra.append(data.spectrum_01_187)
        spectra.append(data.spectrum_01_188)
        spectra.append(data.spectrum_01_189)
        spectra.append(data.spectrum_01_190)
        spectra.append(data.spectrum_01_191)
        spectra.append(data.spectrum_01_192)
        spectra.append(data.spectrum_01_193)
        spectra.append(data.spectrum_01_194)
        spectra.append(data.spectrum_01_195)
        spectra.append(data.spectrum_01_196)
        spectra.append(data.spectrum_01_197)
        spectra.append(data.spectrum_01_198)
        spectra.append(data.spectrum_01_199)
        spectra.append(data.spectrum_01_200)
        spectra.append(data.spectrum_01_201)
        spectra.append(data.spectrum_01_202)
        spectra.append(data.spectrum_01_203)
        spectra.append(data.spectrum_01_204)
        spectra.append(data.spectrum_01_205)
        spectra.append(data.spectrum_01_206)
        spectra.append(data.spectrum_01_207)
        spectra.append(data.spectrum_01_208)
        spectra.append(data.spectrum_01_209)
        spectra.append(data.spectrum_01_210)
        spectra.append(data.spectrum_01_211)
        spectra.append(data.spectrum_01_212)
        spectra.append(data.spectrum_01_213)
        spectra.append(data.spectrum_01_214)
        spectra.append(data.spectrum_01_215)
        spectra.append(data.spectrum_01_216)
        spectra.append(data.spectrum_01_217)
        spectra.append(data.spectrum_01_218)
        spectra.append(data.spectrum_01_219)
        spectra.append(data.spectrum_01_220)
        spectra.append(data.spectrum_01_221)
        spectra.append(data.spectrum_01_222)
        spectra.append(data.spectrum_01_223)
        spectra.append(data.spectrum_01_224)
        spectra.append(data.spectrum_01_225)
        spectra.append(data.spectrum_01_226)
        spectra.append(data.spectrum_01_227)
        spectra.append(data.spectrum_01_228)
        spectra.append(data.spectrum_01_229)
        spectra.append(data.spectrum_01_230)
        spectra.append(data.spectrum_01_231)
        spectra.append(data.spectrum_01_232)
        spectra.append(data.spectrum_01_233)
        spectra.append(data.spectrum_01_234)
        spectra.append(data.spectrum_01_235)
        spectra.append(data.spectrum_01_236)
        spectra.append(data.spectrum_01_237)
        spectra.append(data.spectrum_01_238)
        spectra.append(data.spectrum_01_239)
        spectra.append(data.spectrum_01_240)
        spectra.append(data.spectrum_01_241)
        spectra.append(data.spectrum_01_242)
        spectra.append(data.spectrum_01_243)
        spectra.append(data.spectrum_01_244)
        spectra.append(data.spectrum_01_245)
        spectra.append(data.spectrum_01_246)
        spectra.append(data.spectrum_01_247)
        spectra.append(data.spectrum_01_248)
        spectra.append(data.spectrum_01_249)
        spectra.append(data.spectrum_01_250)
        spectra.append(data.spectrum_01_251)
        spectra.append(data.spectrum_01_252)
        spectra.append(data.spectrum_01_253)
        spectra.append(data.spectrum_01_254)
        spectra.append(data.spectrum_01_255)
        spectra.append(data.spectrum_01_256)
        self.__app.frm_spanview.update_span(spectra, data.center_01, data.span_01)

    def _process_MON_VER(self, data: UBXMessage):
        """
        Process MON-VER sentence - Receiver Software / Hardware version information.

        :param UBXMessage data: MON-VER parsed message
        """

        exts = []
        fw_version = "n/a"
        protocol = "n/a"
        gnss_supported = ""

        try:
            sw_version = (
                getattr(data, "swVersion", "n/a").replace(b"\x00", b"").decode("utf-8")
            )
            sw_version = sw_version.replace("ROM CORE", "ROM")
            sw_version = sw_version.replace("EXT CORE", "Flash")
            hw_version = (
                getattr(data, "hwVersion", "n/a").replace(b"\x00", b"").decode("utf-8")
            )

            for i in range(9):
                idx = "_{0:0=2d}".format(i + 1)
                exts.append(
                    getattr(data, "extension" + idx, b"")
                    .replace(b"\x00", b"")
                    .decode("utf-8")
                )
                if "FWVER=" in exts[i]:
                    fw_version = exts[i].replace("FWVER=", "")
                if "PROTVER=" in exts[i]:
                    protocol = exts[i].replace("PROTVER=", "")
                if "PROTVER " in exts[i]:
                    protocol = exts[i].replace("PROTVER ", "")
                for gnss in ("GPS", "GLO", "GAL", "BDS", "SBAS", "IMES", "QZSS"):
                    if gnss in exts[i]:
                        gnss_supported = gnss_supported + gnss + " "

            # update the UBX config panel
            if self.__app.dlg_ubxconfig is not None:
                self.__app.dlg_ubxconfig.update_pending(
                    "MON-VER",
                    swversion=sw_version,
                    hwversion=hw_version,
                    fwversion=fw_version,
                    protocol=protocol,
                    gnsssupported=gnss_supported,
                )

        except ValueError:
            # self.__app.set_status(ube.UBXMessageError(err), "red")
            pass

    def _process_MON_HW(self, data: UBXMessage):
        """
        Process MON-HW sentence - Receiver Hardware status.

        :param UBXMessage data: MON-HW parsed message
        """

        ant_status = getattr(data, "aStatus", 1)
        ant_power = getattr(data, "aPower", 2)
        jam_ind = getattr(data, "jamInd", 1)

        # update the UBX config panel
        if self.__app.dlg_ubxconfig is not None:
            self.__app.dlg_ubxconfig.update_pending(
                "MON-HW", antstatus=ant_status, antpower=ant_power
            )
