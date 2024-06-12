from gdo.base.GDO_Module import GDO_Module
from gdo.core.Connector import Connector


class module_whatsapp(GDO_Module):

    def gdo_init(self):
        from gdo.whatsapp.connector.WhatsApp import WhatsApp
        Connector.register(WhatsApp)

