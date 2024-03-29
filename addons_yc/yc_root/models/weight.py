# -*- coding: utf-8 -*-


from odoo import models, fields, api
from datetime import datetime as dt


class YcWeight(models.Model):
    _name = "yc.weight"
    _order= "day desc"

    driver_id = fields.Many2one("yc.driver", string="司機名稱")
    name = fields.Char("過磅單號", default=lambda self: self.env["ir.sequence"].next_by_code("WeightList.sequence"))
    day = fields.Date("過磅日期", default=dt.today())
    weightime = fields.Char("過磅時間", default=lambda self: self._get_time())
    person_id = fields.Many2one("yc.hr", string="過磅員")
    weighbridge = fields.Char("地磅序號")
    carno = fields.Char("車次序號")
    in_out = fields.Selection([('I', '進貨'), ('O', '出貨')], '進出貨')
    factory_id = fields.Many2one("yc.factory", string="所屬工廠")
    purchase_times = fields.Integer("進貨次數")
    ship_times = fields.Integer("出貨次數")
    plate_no = fields.Char("車號", related="driver_id.plate_no")
    total = fields.Integer("總重 (KG)")
    curbweight = fields.Integer("空車重 (KG)")
    emptybucket = fields.Integer("空桶重 (KG)")
    net = fields.Integer("淨重 (KG)")
    note = fields.Char("備註")
    refine = fields.Integer("調質重量 (KG)")
    carbur = fields.Integer("滲碳重量")
    other = fields.Integer("其他重量 (KG)")
    other1 = fields.Integer("其他重量1")
    count = fields.Integer("貨重(應等於淨重)", compute="_check_weight")
    # 一張過磅單 上面的貨物可能含有多家客戶
    customer_detail_ids = fields.One2many("yc.weight.details", "name", "客戶明細")

    # 要改成自動編號 & 上鎖
    # @api.multi
    # @api.onchange("name")
    # def _generate(self):
    #     '''WL + 190227 + 001...999
    #                 2    +  6          + 3
    #
    #                 '''
    #     # prefix WL + yymmdd
    #     _serial = 'WL' + dt.today().strftime("%y%m%d")
    #     # search today's last one data on db
    #     obj = self.env['yc.weight'].search([('name', '=like', _serial + "%")], limit=1, order='name DESC')
    #     if obj:  # 如果無/有系列碼
    #         _next = int(obj[0].name[8:]) + 1
    #         _serial += '%03d' % _next
    #     else:
    #         _serial += '001'
    #     self.name = _serial

    @api.model
    def _get_time(self):
        # 不知道為什麼 odoo 有時候會把datetime.now()的時間丟到頁面後會 -8小時
        # 有以上狀況 hour +8 即可解決
        hour = dt.now().hour + 8
        minute = dt.now().minute
        sec = dt.now().second
        if hour > 24:
            hour -= 24

        time = "%02d:%02d:%02d" % (hour, minute, sec)
        return time

    # 車次序號產生
    @api.multi
    @api.onchange("driver_id")
    def _generate_carno(self):
        for rec in self:
            if rec.driver_id:
                year = str(dt.now().year)
                month = "%02d" % (dt.now().month)
                day = "%02d" % (dt.now().day)
                # S1
                if year[3:] == "0":
                    S1 = "A"
                elif year[3:] == "1":
                    S1 = "B"
                elif year[3:] == "2":
                    S1 = "C"
                elif year[3:] == "3":
                    S1 = "D"
                else:
                    S1 = year[3:]

                # S2
                if month == "10":
                    S2 = "A"
                elif month == "11":
                    S2 = "B"
                elif month == "12":
                    S2 = "C"
                else:
                    S2 = month[1:]

                # S3
                day_list = ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'A',
                            'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K',
                            'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V']
                S3 = day_list[int(day) - 1]

                # S4 S5

                S4 = rec.env["yc.driver"].search([('name', '=', rec.driver_id.name)]).code

                check_day = dt.strptime(rec.day, "%Y-%m-%d")
                check = rec.env["yc.weight"].search([('driver_id', '=', rec.driver_id.name), ('day', '=', check_day)])
                if check:
                    S5 = '%02d' % (len(check) + 1)
                else:
                    S5 = "01"

                if S1 and S2 and S3 and S4 and S5:
                    self.carno = str(S1 + S2 + S3 + S4 + S5)
                    rec.carno = self.carno

    # 檢查進出貨分類是否填寫
    @api.constrains("in_out")
    def _verify(self):
        if not self.in_out:
            raise Warning("進出貨分類空值")

    # 進出貨次數自動計算
    @api.multi
    @api.onchange('in_out', 'driver_id')
    def _count(self):
        for rec in self:
            check_day = dt.strptime(rec.day, "%Y-%m-%d")
            pn = self.plate_no
            check_in = self.env["yc.weight"].search(
                [('in_out', '=', 'I'), ('day', '=', check_day), ('plate_no', '=', pn)])
            check_out = self.env["yc.weight"].search(
                [('in_out', '=', 'O'), ('day', '=', check_day), ('plate_no', '=', pn)])

            # 判斷新建還是修改 看單號有沒有在資料庫
            if rec.in_out:  # 進出貨有值
                if pn and rec.day:  # 車牌&日期 有值
                    self.ship_times = len(check_out)
                    self.purchase_times = len(check_in)
                    if not self.env["yc.weight"].search([("name", "=", self.name)]):
                        if rec.in_out == 'I':
                            rec.ship_times = self.ship_times
                            rec.purchase_times = self.purchase_times + 1
                        elif rec.in_out == 'O':
                            # onchange decorator 要存到db 需要rec.field = self.field 這種寫法
                            rec.ship_times = self.ship_times + 1
                            rec.purchase_times = self.purchase_times

    # 選完司機名稱，車牌自動帶入 > 改用related 取代
    # @api.multi
    # @api.onchange("driver_id")
    # def _auto_fetch_plateno(self):
    #     for rec in self:
    #         if self.driver_id:
    #             self.plate_no = self.env["yc.driver"].search([('name', '=', rec.driver_id.name)]).plate_no
    #             rec.plate_no = self.plate_no
    #         else:
    #             pass

    # 淨重自動計算
    @api.onchange("total", "curbweight", "emptybucket")
    def _NetWeight(self):
        self.net = self.total - self.emptybucket - self.curbweight

    # 覆寫新增資料:create()
    # onchange 裝飾中的函式資料是在虛擬record中，在odoo原有create方法中，參數vals抓不到這些onchange所裝飾的函式資料，所以無法存進資料庫
    @api.model
    def create(self, vals):
        _net = vals["total"] - vals["emptybucket"] - vals["curbweight"]
        vals.update({"net": _net})
        return super(YcWeight, self).create(vals)

    # 覆寫修改資料:write()
    # onchange 裝飾中的函式資料是在虛擬record中，在odoo原有write方法中，參數vals抓不到這些onchange所裝飾的函式資料，所以無法存進資料庫
    @api.multi
    def write(self, vals):
        # 沒有修改 vals(dict)就沒有值
        # 如果沒有值 就等於self 如果有值就沿用
        _net_parameter = ["total", "curbweight", "emptybucket"]
        for key in _net_parameter:
            if key in vals:
                pass
            else:
                vals[key] = self[key]
        _net = vals["total"] - vals["emptybucket"] - vals["curbweight"]
        vals.update({"net": _net})
        return super(YcWeight, self).write(vals)

    # 檢查淨重是否等於貨重
    @api.constrains("refine", "carbur", "other", "other1")
    def _verify_weight(self):
        total = self.refine + self.carbur + self.other + self.other1
        if self.net and total != self.net:
            raise Warning("調質重量+滲碳單價+其他重量+其他重量1 應等於 淨重")
        else:
            pass

    # 貨重計算(調值、滲碳、其他、其他1)
    @api.onchange("refine", "carbur", "other", "other1")
    def _check_weight(self):
        total = self.refine + self.carbur + self.other + self.other1
        self.count = total

    # many2one這個資料庫時 會用這裡的name 而不是(name)單號
    # 和 _rec_name = "carno" 一樣效果
    @api.multi
    def name_get(self):
        result = []
        for record in self:
            # 轉檔時 self._context.get('params')['action'] = 107
            # 過磅時 self._context.get('params')['action'] = 82
            # 進貨創建時 self._context.get('params') = None
            # 進貨瀏覽時 self._context.get('params')['action'] = 81
            if not self._context.get('params') or self._context.get('params')['action'] == 81:
                name = record.carno
                result.append((record.id, name))
            else:
                name = record.name
                result.append((record.id, name))
        return result


class YcWeightDetails(models.Model):
    _name = "yc.weight.details"

    name = fields.Many2one("yc.weight", "訂單編號", ondelete='cascade')
    no = fields.Integer("序號", default=1)
    compute_no = fields.Integer("最大數", compute= "_get_row_no")
    customer_id = fields.Many2one("yc.customer", "客戶名稱")
    processing_id = fields.Many2one("yc.processing", "加工廠名稱")
    note = fields.Char("備註")

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            processing = record.env['yc.processing'].search([('code', '=', record.processing_id.code)])
            name = processing.name
            result.append((record.id, name))
        return result

    @api.depends("compute_no")
    def _get_row_no(self):
        if self.ids:
            count =1
            for rec in self:
                weight_id = self.env['yc.weight.details'].search([('id','=', rec.id)])
                weight_id.write({'no': count})
                count+=1