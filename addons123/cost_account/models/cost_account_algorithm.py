# coding:utf-8
from odoo import api, fields, models,_


class cost_account_algorithm(models.Model):
    _name = "cost.account.algorithm"

    execute_date = fields.Datetime("执行时间")
    state = fields.Selection([('1', '成功'), ('2', '失败')], string="执行状态")

    @api.multi
    def cost_account_algorithm(self):
        try:
            # 取得成本中心
            cost_centers = self.env['cost.center'].search([])
            for cost_center in cost_centers:
                # 计算陈本。分摊人工费、折旧费、公共耗材费、其他费用
                self._cost_account(cost_center)
                # 当成本中心的成品计算完成后，分摊废品，废品分配完成后重新计算成本并存到数据库中
                # 取得废品费用分配方式
                waste_expense_distribution = self.env['waste.expense.distribution'].search([('cost_center_id', '=', cost_center.id)])
                # 取得废品的费用
                mrp_productions = self.env['mrp.production'].search(
                    [('cost_center_id', '=', cost_center.id), ('state', '=', 'done'), ('cost_account', '=', True)])
                # 实际工时
                time_sheet = self.env['time.sheet'].search([('cost_center_id', '=', cost_center.id)])
                scrap_total_amount = 0.0  # 废品总额
                product_count = 0.0  # 成品总数
                for mrp_production in mrp_productions:
                    # 取得报废的产品
                    scrap = self.env['stock.scrap'].search([('production_id', '=', mrp_production.id), ('product_id', '=', mrp_production.product_id.id)])
                    if scrap:
                        scrap_total_amount += scrap.cost
                        product_count += mrp_production.move_finished_ids[0].quantity_done
                        # 定义产品和数量的字典，该方法可以将KEY相同的数据相加。这样就可以计算出产品的数量了。
                        product_count_dict = self.union_dict(product_count_dict, {
                            mrp_production.product_id.id: mrp_production.move_finished_ids[0].quantity_done})
                # 非配方式说明，1：按产品产量、2：按实际工时、3：按定额工时、4：按产品权重
                scrap_ft_ratio = {}
                if waste_expense_distribution == "1":
                    scrap_ft_ratio["all"] = scrap_total_amount / product_count
                if waste_expense_distribution == "2":
                    # 实际工时
                    actual_time_total = 0.0
                    for actual_time in time_sheet:
                        actual_time_total += actual_time.actual_time
                    for at in time_sheet:
                        scrap_ft_ratio["all"] = scrap_total_amount * at.actual_time / actual_time_total
                if waste_expense_distribution == "4":
                    # 权重分摊计算公式：金额 / (各产品的权重和数量乘积之和) * 产品权重*产品数量
                    weight_total = 0.0
                    for allocation_id in waste_expense_distribution.allocation_id:
                        weight_total += allocation_id.percent * product_count_dict[allocation_id.product_id.id]
                    for allocation_id in waste_expense_distribution.allocation_id:
                        for mrp_production_id in mrp_productions:
                            if mrp_production_id.product_id.id == allocation_id.product_id.id:
                                scrap_ft_ratio[mrp_production_id.id] = scrap_total_amount / weight_total * allocation_id.percent
                for mrp_production in mrp_productions:
                    stock_moves = self.env['stock.move'].search(
                        [('production_id', '=', mrp_production_id.id), ('scrapped', '=', False)])
                    # 计算出每个产品需要分摊多少
                    for stock_move in stock_moves:
                        if waste_expense_distribution == "1" or waste_expense_distribution == "2":
                            product_cost = stock_moves.cost_test + scrap_ft_ratio["all"] * mrp_production.product_qty
                        else:
                            product_cost = stock_moves.cost_test + scrap_ft_ratio[mrp_production_id.id] * mrp_production.product_qty
                        stock_move.write(
                            {'estimated_price': product_cost, 'cost': product_cost, 'cost_test': product_cost})
            # 成本核算完成后，做记账操作

            self.write({'state': "1"})
        except:
            self.write({'state': "2"})
        return True

    def _cost_account(self, cost_center):
        # 取得产品中心的各项费用分配方式
        # 人工费用分配方式
        manual_distribution = self.env['manual.distribution'].search([('cost_center_id', '=', cost_center.id)])
        # 折旧费用分配方式
        expense_distribution = self.env['expense.distribution'].search([('cost_center_id', '=', cost_center.id)])
        # 公共耗材分配方式
        material_distribution = self.env['material.distribution'].search([('cost_center_id', '=', cost_center.id)])
        # 其他费用分配方式
        other_expense_distribution = self.env['other.expense.distribution'].search(
            [('cost_center_id', '=', cost_center.id)])
        # -------------------------------------------------------------------------我是美丽的分割线-------------------------------------------------------------------------
        # 取得产品中心各项费用
        # 人工费用
        labor_cost = self.env['labor.cost'].search([('cost_center_id', '=', cost_center.id)])
        # 折旧费用
        depreciation_expense = self.env['depreciation.expense'].search([('cost_center_id', '=', cost_center.id)])
        # 公共耗材
        material_consumption = self.env['material.consumption'].search([('cost_center_id', '=', cost_center.id)])
        # 其他费用
        other_expense = self.env['other.expense'].search([('cost_center_id', '=', cost_center.id)])
        # 实际工时
        time_sheet = self.env['time.sheet'].search([('cost_center_id', '=', cost_center.id)])
        # 按照成本中心的产量分配，需要取得该产品中心生产的所有产品和各产品的数量

        # -------------------------------------------------------------------------我是美丽的分割线-------------------------------------------------------------------------
        mrp_productions = self.env['mrp.production'].search(
            [('cost_center_id', '=', cost_center.id), ('state', '=', 'done'), ('cost_account', '=', False)])
        if mrp_productions:
            # 取得产品id的列表并去重
            product_ids = []
            mrp_production_ids = []
            product_count = 0
            product_count_dict = {}
            for production in mrp_productions:
                # 判断该订单的物料清单中的产品是否是物料，如果是物料将产品ID添加到list中，如果不是，则跳过
                flg = True
                for material_id in production.move_raw_ids:
                    if not material_id.cost:
                        flg = False
                if flg:
                    mrp_production_ids.append(production)
                # product_ids.append(production.product_id.id)
                product_count += production.move_finished_ids[0].quantity_done
                # 定义产品和数量的字典，该方法可以将KEY相同的数据相加。这样就可以计算出产品的数量了。
                product_count_dict = self.union_dict(product_count_dict, {production.product_id.id: production.move_finished_ids[0].quantity_done})
            # 循环完成产品，取得所有的产品的id，然后去重复取得生产了多少种产品
            # product_ids = list(set(product_ids))
            mrp_production_ids = list(set(mrp_production_ids))
            if not mrp_production_ids:
                return
            # 开始计算
            # 非配方式说明，1：按产品产量、2：按实际工时、3：按定额工时、4：按产品权重
            # -------------------------------------------------------------------------我是美丽的分割线-------------------------------------------------------------------------
            # 人工费用
            cost_ratio_labor = {}
            cost_ratio_manager = {}
            if manual_distribution.type == "1":
                for mrp_production_id in mrp_production_ids:
                    # 算出直接人工费用分摊比例
                    cost_ratio_labor[mrp_production_id.id] = float(labor_cost.labor_expense) / product_count
                    # 算出管理人员工资分摊比例
                    cost_ratio_manager[mrp_production_id.id] = float(labor_cost.manage_expense) / product_count
            elif manual_distribution.type == "2":
                # 实际工时
                actual_time_total = 0.0
                for actual_time in time_sheet:
                    actual_time_total += actual_time.actual_time
                for at in time_sheet:
                    cost_ratio_labor[at.order_id] = float(labor_cost.labor_expense) * at.actual_time / actual_time_total
                    cost_ratio_manager[at.order_id] = float(labor_cost.manage_expense) * at.actual_time / actual_time_total
            elif manual_distribution.type == "4":
                # 权重分摊计算公式：金额 / (各产品的权重和数量乘积之和) * 产品权重*产品数量
                weight_total = 0.0
                for allocation_id in manual_distribution.allocation_id:
                    weight_total += allocation_id.percent * product_count_dict[allocation_id.product_id.id]
                for allocation_id in manual_distribution.allocation_id:
                    for mrp_production_id in mrp_production_ids:
                        if mrp_production_id.product_id.id == allocation_id.product_id.id:
                            cost_ratio_labor[mrp_production_id.id] = float(labor_cost.labor_expense) / weight_total * allocation_id.percent
                            cost_ratio_manager[mrp_production_id.id] = float(labor_cost.manage_expense) / weight_total * allocation_id.percent
            # -------------------------------------------------------------------------我是美丽的分割线-------------------------------------------------------------------------
            # 折旧费
            depreciation_ratio = {}
            if expense_distribution.type == "1":
                for mrp_production_id in mrp_production_ids:
                    # 算出折旧费用分摊比例
                    depreciation_ratio[mrp_production_id.id] = float(depreciation_expense.old_expense) / product_count
            elif expense_distribution.type == "2":
                # 实际工时
                actual_time_total = 0.0
                for actual_time in time_sheet:
                    actual_time_total += actual_time.actual_time
                for at in time_sheet:
                    depreciation_ratio[at.order_id] = float(depreciation_expense.old_expense) * at.actual_time / actual_time_total
            elif expense_distribution.type == "4":
                # 权重分摊计算公式：金额 / (各产品的权重和数量乘积之和) * 产品权重*产品数量
                weight_total = 0.0
                for allocation_id in expense_distribution.allocation_id:
                    weight_total += allocation_id.percent * product_count_dict[allocation_id.product_id.id]
                for allocation_id in expense_distribution.allocation_id:
                    for mrp_production_id in mrp_production_ids:
                        if mrp_production_id.product_id.id == allocation_id.product_id.id:
                            depreciation_ratio[mrp_production_id.id] = float(depreciation_expense.old_expense) / weight_total * allocation_id.percent
            # -------------------------------------------------------------------------我是美丽的分割线-------------------------------------------------------------------------
            # 其他费用
            other_expense_ratio = {}
            if other_expense_distribution.type == "1":
                for mrp_production_id in mrp_production_ids:
                    # 算出其他费用分摊比例
                    other_expense_ratio[mrp_production_id.id] = float(other_expense.expense) / product_count
            elif other_expense_distribution.type == "2":
                # 实际工时
                actual_time_total = 0.0
                for actual_time in time_sheet:
                    actual_time_total += actual_time.actual_time
                for at in time_sheet:
                    other_expense_ratio[at.order_id] = float(other_expense.expense) * at.actual_time / actual_time_total
            elif other_expense_distribution.type == "4":
                # 权重分摊计算公式：金额 / (各产品的权重和数量乘积之和) * 产品权重*产品数量
                weight_total = 0.0
                for allocation_id in other_expense_distribution.allocation_id:
                    weight_total += allocation_id.percent * product_count_dict[allocation_id.product_id.id]
                for allocation_id in other_expense_distribution.allocation_id:
                    for mrp_production_id in mrp_production_ids:
                        if mrp_production_id.product_id.id == allocation_id.product_id.id:
                            other_expense_ratio[mrp_production_id.id] = float(other_expense.expense) / weight_total * allocation_id.percent
            # -------------------------------------------------------------------------我是美丽的分割线-------------------------------------------------------------------------
            # 公共耗材
            material_consumption_ratio = {}
            if material_distribution.type == "1":
                for mrp_production_id in mrp_production_ids:
                    material_consumption_ratio[mrp_production_id.id] = float(material_consumption.expense) / product_count
            elif material_distribution.type == "2":
                # 实际工时
                actual_time_total = 0.0
                for actual_time in time_sheet:
                    actual_time_total += actual_time.actual_time
                for at in time_sheet:
                    material_consumption_ratio[at.order_id] = float(material_consumption.expense) * at.actual_time / actual_time_total
            elif material_distribution.type =="4":
                # 权重分摊计算公式：金额 / (各产品的权重和数量乘积之和) * 产品权重*产品数量
                weight_total = 0.0
                for allocation_id in material_distribution.allocation_id:
                    weight_total += allocation_id.percent * product_count_dict[allocation_id.product_id.id]
                for allocation_id in material_distribution.allocation_id:
                    for mrp_production_id in mrp_production_ids:
                        if mrp_production_id.product_id.id == allocation_id.product_id.id:
                            material_consumption_ratio[mrp_production_id.id] = float(material_consumption.expense) / weight_total * allocation_id.percent
            # -------------------------------------------------------------------------我是美丽的分割线-------------------------------------------------------------------------
            for mrp_production_id in mrp_production_ids:
                # 物料成本合计
                material_cost_total = 0.0
                for move_raw_id in mrp_production_id.move_raw_ids:
                    material_cost_total += move_raw_id.cost * move_raw_id.quantity_done
                # 取得废料，算出废料成本总计
                stock_scraps = self.env['stock.scrap'].search([('production_id', '=', mrp_production_id.id)])
                meterial_scrap_total = 0.0
                for stock_scrap in stock_scraps:
                    if stock_scrap.product_id != mrp_production_id.product_id.id:
                        meterial_scrap_total = stock_scrap.move_id.cost * stock_scrap.scrap.qty
                # 完成产品合计
                finished_total = 0.0
                for move_finished_id in mrp_production_id.move_finished_ids:
                    finished_total += move_finished_id.quantity_done
                # 需要分摊费用总和
                material_cost_total += meterial_scrap_total + (cost_ratio_labor[mrp_production_id.id] + cost_ratio_manager[mrp_production_id.id]
                                        + depreciation_ratio[mrp_production_id.id]
                                        + other_expense_ratio[mrp_production_id.id]
                                        + material_consumption_ratio[mrp_production_id.id]) * finished_total
                stock_moves = self.env['stock.move'].search([('production_id', '=', mrp_production_id.id), ('scrapped', '=', False)])
                # 计算出每个产品需要分摊多少
                product_cost = material_cost_total / finished_total
                for stock_move in stock_moves:
                    stock_move.write({'estimated_price': product_cost, 'cost': product_cost, 'cost_test': product_cost})
                stock_scrap_infos = self.env['stock.scrap'].search([('production_id', '=', mrp_production_id.id), ('product_id', '=', mrp_production_id.product_id.id)])
                for stock_scrap_info in stock_scrap_infos:
                    stock_scrap_info.move_id.write({'estimated_price': product_cost, 'cost': product_cost, 'cost_test': product_cost})
                mrp_production_id.write({"cost_account": True})
                self._cr.commit()
            self._cost_account(cost_center)

    # key相同的value相加
    def union_dict(self, *objs):
        _keys = set(sum([obj.keys() for obj in objs],[]))
        _total = {}
        for _key in _keys:
            _total[_key] = sum([obj.get(_key,0) for obj in objs])
        return _total