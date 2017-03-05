odoo.define('driserp.driserp', function (require) {
"use strict";

var core = require('web.core');
var data = require('web.data');
var formats = require('web.formats');
var pyeval = require('web.pyeval');
var session = require('web.session');
var View = require('web.View');

var Model = require('web.DataModel');
var TreeView = require('web.ListView');
var ControlPanelMixin = require('web.ControlPanelMixin');
var FormView = require('web.FormView');
var Widget = require('web.Widget');

var _lt = core._lt;
var QWeb = core.qweb;

var CombineListView = TreeView.extend({
    display_name: _lt('Combine_orders'),
    render_buttons: function ($node) {
        if (!this.$buttons) {
            this.$buttons = $(QWeb.render("CompareListView.buttons", {'widget': this}));

            this.$buttons.find('.combine_order').click(this.proxy('combine_order'));

            $node = $node || this.options.$buttons;
            if ($node) {
                this.$buttons.appendTo($node);
            } else {
                this.$('.oe_list_buttons').replaceWith(this.$buttons);
            }
        }
    },

    combine_order: function () {
        var self = this;
        var context = self.dataset.context;
        context['records'] = self.groups.get_selection().ids;
        if(context['records']!=undefined){
            if(context['records'].length <= 1){
                self.ViewManager.do_warn("Error", '选择订单数量不足', 1);
            }
            else{
                new Model(self.dataset.model).call("combine_order",[self.dataset.context.tender_id,context]).then(function(result) {
                    self.ViewManager.do_action(self.ViewManager.action.id);
                    self.ViewManager.action_manager.history_back();
                });
            }
        }
    },
});

core.view_registry.add('combine_orders', CombineListView);

return CombineListView;
});
