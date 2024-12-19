from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.base.Trans import t
from gdo.whatsapp.GDT_WAPhoneNumber import GDT_WAPhoneNumber
from gdo.whatsapp.connector.WhatsApp import WhatsApp


class invite(Method):

    def gdo_trigger(self) -> str:
        return 'wapp.invite'

    def gdo_user_permission(self) -> str | None:
        return 'staff'

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_WAPhoneNumber('phone'),
        ]

    def gdo_execute(self) -> GDT:
        wapp = WhatsApp.instance()
        invite_text = t('whatsapp_invite_text')
        wapp.send_to_number(self.param_value('phone'), invite_text)
        return self.msg('msg_user_invited')
