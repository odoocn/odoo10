/**
 * Created by zhang on 2016/12/2.
 */
function new_token(){
    window.open("request_auth?shop_id="+$('.shops_id_field').html()+"&req_url=http://"+window.location.host);
    // window.location.href="request_auth?shop_id="+$('.shops_id_field').html()+"&req_url=http://"+window.location.host
}