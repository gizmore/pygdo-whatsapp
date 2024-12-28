import os

from gdo.base.GDO_Module import GDO_Module
from gdo.core.Connector import Connector
from gdo.core.GDO_Server import GDO_Server


class module_whatsapp(GDO_Module):

    def gdo_init(self):
        from gdo.whatsapp.connector.WhatsApp import WhatsApp
        Connector.register(WhatsApp)

    def gdo_install(self):
        if not GDO_Server.get_by_connector('whatsapp'):
            GDO_Server.blank({
                'serv_name': 'WhatsApp',
                'serv_connector': 'whatsapp',
            }).insert()
        fifo_in = self.file_path('bin/wapp.in')
        fifo_out = self.file_path('bin/wapp.out')
        for fifo_file in [fifo_in, fifo_out]:
            if not os.path.exists(fifo_file):
                os.mkfifo(fifo_file)
