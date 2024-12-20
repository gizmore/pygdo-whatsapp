from gdo.base.Util import Strings
from gdo.core.GDT_String import GDT_String


class GDT_WAPhoneNumber(GDT_String):
    APPENDIX = '@c.us'

    def __init__(self, name):
        super().__init__(name)
        self.maxlen(28)
        self.minlen(8)
        self.ascii()

    async def get_value(self):
        phone = self.get_val()
        if not phone.endswith(self.APPENDIX):
            phone += self.APPENDIX
        return phone

    def get_phone_number(self):
        val = self.get_val()
        return '00' + Strings.substr_to(val, self.APPENDIX, val)
