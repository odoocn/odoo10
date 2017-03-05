window.onload=function(){
    var  i=0;
    var  jfnum=0.0;
    var  dfnum=0.0;
    $("span[name='jf']").each(function() {
        jfnum=jfnum+parseFloat($(this).text());
        i++;
    });
    $("span[name='df']").each(function() {
        dfnum=dfnum+parseFloat($(this).text());
    });
    if(i%5>0){
        var str='';
        for(var num=0;num<(5-(i%5));num++){
              str=str+"<tr height='30px'><td  style='border-collapse:collapse; border:1px solid #000; line-height:50px;padding:0 0 0 5px; font-size:18px;'> </td><td   style='border-collapse:collapse; border:1px solid #000;height:50px; line-height:50px;padding:0 0 0 5px; font-size:18px;'> </td><td   style='border-collapse:collapse; border:1px solid #000;height:50px; line-height:50px;padding:0 0 0 5px; font-size:18px;'> </td><td   style='border-collapse:collapse; border:1px solid #000;height:50px; line-height:50px;padding:0 0 0 5px; font-size:18px;'> </td></tr>"
        }
        $('tbody[name="tradd"]')[Math.floor(i/5)].innerHTML=str;
     }


    $('span[name="jfsum"]')[Math.floor(i/5)].innerHTML=jfnum;
    $('span[name="dfsum"]')[Math.floor(i/5)].innerHTML=dfnum;
    var rmb=convertCurrency(jfnum);
    $('span[name="allsum"]')[Math.floor(i/5)].innerHTML=rmb;
    for(var n=0;n<Math.ceil(i/5);n++){
        $('span[name="xhnum"]')[n].innerHTML=n+1;
    }
}
function accAdd(arg1, arg2) {
    var r1, r2, m;
    try {
        r1 = arg1.toString().split(".")[1].length;
    }
    catch (e) {
        r1 = 0;
    }
    try {
        r2 = arg2.toString().split(".")[1].length;
    }
    catch (e) {
        r2 = 0;
    }
    m = Math.pow(10, Math.max(r1, r2));
    return (arg1 * m + arg2 * m) / m;
}

function convertCurrency(currencyDigits) {

    var MAXIMUM_NUMBER = 99999999999.99;  //最大值
    // 定义转移字符
    var CN_ZERO = "零";
    var CN_ONE = "壹";
    var CN_TWO = "贰";
    var CN_THREE = "叁";
    var CN_FOUR = "肆";
    var CN_FIVE = "伍";
    var CN_SIX = "陆";
    var CN_SEVEN = "柒";
    var CN_EIGHT = "捌";
    var CN_NINE = "玖";
    var CN_TEN = "拾";
    var CN_HUNDRED = "佰";
    var CN_THOUSAND = "仟";
    var CN_TEN_THOUSAND = "万";
    var CN_HUNDRED_MILLION = "亿";
    var CN_DOLLAR = "元";
    var CN_TEN_CENT = "角";
    var CN_CENT = "分";
    var CN_INTEGER = "整";

    // 初始化验证:
    var integral, decimal, outputCharacters, parts;
    var digits, radices, bigRadices, decimals;
    var zeroCount;
    var i, p, d;
    var quotient, modulus;

    // 验证输入字符串是否合法
    if (currencyDigits.toString() == "") {
        alert("还没有输入数字");
        $("#Digits").focus();
        return;
    }
    //判断输入的数字是否大于定义的数值
    if (Number(currencyDigits) > MAXIMUM_NUMBER) {
        alert("您输入的数字太大了");
        $("#Digits").focus();
        return;
    }
    if(currencyDigits.toString().indexOf(".") > 0 ){
        parts = currencyDigits.split(".");
        if (parts.length > 1) {
            integral = parts[0];
            decimal = parts[1];
            decimal = decimal.substr(0, 2);
        }
    }else {
            integral = currencyDigits;
            decimal = "";
    }

    // 实例化字符大写人民币汉字对应的数字
    digits = new Array(CN_ZERO, CN_ONE, CN_TWO, CN_THREE, CN_FOUR, CN_FIVE, CN_SIX, CN_SEVEN, CN_EIGHT, CN_NINE);
    radices = new Array("", CN_TEN, CN_HUNDRED, CN_THOUSAND);
    bigRadices = new Array("", CN_TEN_THOUSAND, CN_HUNDRED_MILLION);
    decimals = new Array(CN_TEN_CENT, CN_CENT);

    outputCharacters = "";
    //大于零处理逻辑
    if (Number(integral) > 0) {
        zeroCount = 0;
        for (i = 0; i < integral.toString().length; i++) {
            p = integral.toString().length - i - 1;
            d = integral.toString().substr(i, 1);
            quotient = p / 4;
            modulus = p % 4;
            if (d == "0") {
                zeroCount++;
            }
            else {
                if (zeroCount > 0) {
                    outputCharacters += digits[0];
                }
                zeroCount = 0;
                outputCharacters += digits[Number(d)] + radices[modulus];
            }
            if (modulus == 0 && zeroCount < 4) {
                outputCharacters += bigRadices[quotient];
            }
        }
        outputCharacters += CN_DOLLAR;
    }
    // 包含小数部分处理逻辑
    if (decimal != "") {
        for (i = 0; i < decimal.length; i++) {
            d = decimal.substr(i, 1);
            if (d != "0") {
                outputCharacters += digits[Number(d)] + decimals[i];
            }
        }
    }
    //确认并返回最终的输出字符串
    if (outputCharacters == "") {
        outputCharacters = CN_ZERO + CN_DOLLAR;
    }
    if (decimal == "") {
        outputCharacters += CN_INTEGER;
    }

    //获取人民币大写
    //$("#getCapital").val(outputCharacters);
    return outputCharacters;
}