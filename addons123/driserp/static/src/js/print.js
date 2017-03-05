function Sprint(paper){
    var jobid="";var status="";var temp = 0;
    var jobTask;var exitTask;
    LODOP = getLodop();
	LODOP.PRINT_INIT("");
	LODOP.SET_PRINT_PAGESIZE(3, "10cm","20cm",'SF_express');
	LODOP.ADD_PRINT_HTM("1cm",0,"100%","100%",paper);
    LODOP.SET_PRINT_MODE("CATCH_PRINT_STATUS",true);
    LODOP.On_Return_Remain=true;
//    LODOP.On_Return=function(TaskID,Value){
//        if(TaskID==jobTask){
//            jobid=Value;
//            document.getElementById('T1').value=jobid;
//            while(status!="148" && status!="8208"){
//                LODOP.On_Return=function(Taskid,value){
//                    status=value;
//                };
//                LODOP.GET_VALUE("PRINT_STATUS_ID",jobid);
//                temp += 1;
//                if (temp == 200){
//                    break;
//                }
//            }
//            document.getElementById('T2').value=status;
//        }
//    };
    jobTask=LODOP.PRINTA();
    //exitTask=LODOP.GET_VALUE("PRINT_STATUS_EXIST",jobid);
};
