/**
 * Created by Vnsoft on 2016/4/28.
 */
odoo.vnsoft_form_hide_edit = function(instance){
    alert(123)
    instance.web.FormView.include({
            do_push_state: function (state) {
                var self = this;
                this._super.apply(this, arguments);
                var no_edit = undefined;
                if (this.options.action != null && this.options.action.context != null && (this.options.action.context.active_id == undefined || this.options.action.target != "new")){
                    no_edit = this.options.action.context.form_no_edit
                }
                if(no_edit!=undefined){
                    try{
                        var result = this.compute_domain(no_edit);
                        if(result==true){
                            if(this.get("actual_mode")!="view"){
                                this.$buttons.find('.o_form_button_cancel').trigger('click')
                            }
                            this.$buttons.find(".o_form_buttons_view").hide()
                        }else{
                            if(this.get("actual_mode")=="view") {
                                this.$buttons.find(".o_form_buttons_view").show()
                            }
                        }
                    }catch(e){

                    }

                }
            }
        }
    );

}