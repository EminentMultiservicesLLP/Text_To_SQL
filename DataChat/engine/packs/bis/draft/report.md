# Draft pack report: bis

Scanned schemas: public. Tables: 351. Proposed subject areas: 8.

## Proposed subject areas

- **Smtbmemployee** (`public.smtbmemployee`), date column `smtbmemployee.dateofbirth`, 6 measures
- **Smtbmcustbrloc** (`public.smtbmcustbrloc`), date column `smtbmcustbrloc.datecreated`, 7 measures
- **Smtbmcustomer** (`public.smtbmcustomer`), date column `smtbmcustomer.datecreated`, 2 measures
- **Smtbtworkorderhdr** (`public.smtbtworkorderhdr`), date column `smtbtworkorderhdr.wodate`, 4 measures
- **Smtbmbank** (`public.smtbmbank`), date column `smtbmbank.datecreated`, 3 measures
- **Smtbmsalaryhead** (`public.smtbmsalaryhead`), date column `smtbmsalaryhead.datecreated`, 4 measures
- **Smtbtarrears** (`public.smtbtarrears`), date column `smtbtarrears.transdate`, 2 measures
- **Smtbmcompany** (`public.smtbmcompany`), date column `smtbmcompany.datecreated`, 2 measures

## Joins guessed from column names (check each one)

- `public.smtbtdailyattendance.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtdailyattendance.empid` → `public.smtbmemployee.empid`
- `public.smtbtdailyattendance.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtdailyattendance.wohdrid` → `public.smtbtworkorderhdr.wohdrid`
- `public.smtbtdailyattendance.wodtlid` → `public.smtbtworkorderdtl.wodtlid`
- `public.smtbtdailyattendance.resourceid` → `public.smtbmresource.resourceid`
- `public.smtbtdailyattendance.attstatusid` → `public.smtbgattendancestatus.attstatusid`
- `public.smtbtdailyattendance.shiftid` → `public.smtbmshift.shiftid`
- `public.smtbtdailyattendance.custshiftid` → `public.smtbmcustomershift.custshiftid`
- `public.smtbtsalarypaymentdtl.leaveprocessid` → `public.smtbtemployeeleavesalary.leaveprocessid`
- `public.smtbtsalarypaymentdtl.bonusprocessid` → `public.smtbtemployeebonussalary.bonusprocessid`
- `public.smtbtsalarypaymentdtl.fullfinalprocessid` → `public.smtbtemployeefullfinalsalary.fullfinalprocessid`
- `public.smtbtsalarypaymentdtl.advanceid` → `public.smtbtadvance.advanceid`
- `public.smtbmcustlocgrouphdr.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtarrearssalarydtl.arrears_id` → `public.smtbtarrears.arrearid`
- `public.smtbtarrearssalarydtl.empid` → `public.smtbmemployee.empid`
- `public.smtbtarrearssalarydtl.resourceid` → `public.smtbmresource.resourceid`
- `public.smtbtemployeebonussummaryhistory.bonusprocessid` → `public.smtbtemployeebonussalary.bonusprocessid`
- `public.smtbtemployeebonussummaryhistory.empid` → `public.smtbmemployee.empid`
- `public.smtbminvoiceconsogrptmp.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbminvoiceconsogrptmp.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbminvoiceconsogrptmp.stateid` → `public.smtbmstate.stateid`
- `public.smtbmempsalaryheaddtl.empid` → `public.smtbmemployee.empid`
- `public.smtbmempsalaryheaddtl.gradeid` → `public.smtbmgradehdr.gradeid`
- `public.smtbmempsalaryheaddtl.salaryheadid` → `public.smtbmsalaryhead.salaryheadid`
- `public.smtbmbranchcode.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtbghdr.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbtbghdr.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtbghdr.bankbrid` → `public.smtbmbank.bankbrid`
- `public.smtbtbghdr.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtbghdr.typeid` → `public.smtbmtype.typeid`
- `public.payroll_run.branch_id` → `public.smtbmbranch.brlocid`
- `public.payroll_run.job_code` → `public.background_job_definition.job_code`
- `public.smtbttrainingdtl.empid` → `public.smtbmemployee.empid`
- `public.smtbttrainingdtl.trainingtypeid` → `public.smtbmtrainingtype.trainingtypeid`
- `public.smtbmleaveslab_details.leave_slab_id` → `public.smtbmleaveslab_master.leave_slab_id`
- `public.smtbmempsalaryheaddtltemp.empsaldtlid` → `public.smtbmempsalaryheaddtl.empsaldtlid`
- `public.smtbmempsalaryheaddtltemp.empid` → `public.smtbmemployee.empid`
- `public.smtbmempsalaryheaddtltemp.salaryheadid` → `public.smtbmsalaryhead.salaryheadid`
- `public.smtbtcreditdebitreceiptno.invpayhdrid` → `public.smtbtcustinvpaymenthdr.invpayhdrid`
- `public.smtbtcreditdebitreceiptno.stateid` → `public.smtbmstate.stateid`
- `public.smtbtcreditdebitreceiptno.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtcreditdebitreceiptno.companyid` → `public.smtbmcompany.companyid`
- `public.smtbmmonthlyratedtl.monthlyratecardhdrid` → `public.smtbmmonthlyratehdr.monthlyratecardhdrid`
- `public.smtbmmonthlyratedtl.ratecardid` → `public.smtbmratecard.ratecardid`
- `public.smtbguserdefinedrptperm.reportid` → `public.smtbgreportformat.reportid`
- `public.smtbguserdefinedrptperm.userid` → `public.smtbmusers.userid`
- `public.smtbmcustbrlochistory.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbmcustbrlochistory.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbmcustbrlochistory.custlocgroupid` → `public.smtbmcustlocgroup.custlocgroupid`
- `public.smtbmcustbrlochistory.cityid` → `public.smtbmcity.cityid`
- `public.smtbmcustbrlochistory.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbmcustbrlochistory.neftmasterid` → `public.smtbmneftmaster.neftmasterid`
- `public.smtbtinquiry.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtinquiry.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbtinquiry.cityid` → `public.smtbmcity.cityid`
- `public.smtbtinquiry.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbmleaveslab_master.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.brs_momentorder.empid` → `public.smtbmemployee.empid`
- `public.brs_momentorder.branchid` → `public.smtbmbranch.brlocid`
- `public.smtbmcustbrlocgstdet.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbmcustbrlocgstdet.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbmcustbrlocgstdet.cityid` → `public.smtbmcity.cityid`
- `public.smtbmcustbrlocgstdet.stateid` → `public.smtbmstate.stateid`
- `public.smtbmcustbrlocgstdet.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbmbranch.companyid` → `public.smtbmcompany.companyid`
- `public.smtbmbranch.cityid` → `public.smtbmcity.cityid`
- `public.smtbmbranch.finyearid` → `public.smtbgfinyear.finyearid`
- `public.smtbmratecharthdr.stateid` → `public.smtbmstate.stateid`
- `public.smtbmratecharthdr.resourceid` → `public.smtbmresource.resourceid`
- `public.smtbmratecharthdr.ratezoneid` → `public.smtbmratezone.ratezoneid`
- `public.smtbminsuranceskipdtl.insuranceid` → `public.smtbminsurance.insuranceid`
- `public.smtbgunlocktransactions.transid` → `public.smtbgactiveuser.transid`
- `public.smtbgunlocktransactions.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbgunlocktransactions.userid` → `public.smtbmusers.userid`
- `public.newcontract.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtpurchaseorderdtl.pohdrid` → `public.smtbtpurchaseorderhdr.pohdrid`
- `public.smtbtpurchaseorderdtl.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtpurchaseorderdtl.resourceid` → `public.smtbmresource.resourceid`
- `public.smtbtpurchaseorderdtl.ratecharthdrid` → `public.smtbmratecharthdr.ratecharthdrid`
- `public.smtbtpurchaseorderdtl.attstatusid` → `public.smtbgattendancestatus.attstatusid`
- `public.smtbtemployeeleavesalary.empid` → `public.smtbmemployee.empid`
- `public.smtbtemployeeleavesalary.customer_id` → `public.smtbmcustomer.customerid`
- `public.smtbtemployeeleavesalary.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtemployeeleavesalary.companyid` → `public.smtbmcompany.companyid`
- `public.smtbtemployeebonusmaster1.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtemployeebonusmaster1.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbtemployeebonusmaster1.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbmrecoveryusedagcn.empid` → `public.smtbmemployee.empid`
- `public.smtbmrecoveryusedagcn.loanid` → `public.smtbtcashdetails.loanid`
- `public.smtbmgradehdr.resourceid` → `public.smtbmresource.resourceid`
- `public.smtbtarrearsdetailchild.arrearid` → `public.smtbtarrears.arrearid`
- `public.smtbtarrearsdetailchild.empid` → `public.smtbmemployee.empid`
- `public.smtbtarrearsdetailchild.companyid` → `public.smtbmcompany.companyid`
- `public.smtbtarrearsdetailchild.resourceid` → `public.smtbmresource.resourceid`
- `public.empdob.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtdeploymenthdr.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtdeploymenthdr.wohdrid` → `public.smtbtworkorderhdr.wohdrid`
- `public.smtbtdeploymenthdr.empid` → `public.smtbmemployee.empid`
- `public.smtbtratebreakup.transid` → `public.smtbgactiveuser.transid`
- `public.smtbtratebreakup.ratecardid` → `public.smtbmratecard.ratecardid`
- `public.smtbtworkorderhdr.finyearid` → `public.smtbgfinyear.finyearid`
- `public.smtbtworkorderhdr.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtworkorderhdr.quotationid` → `public.smtbtquotation.quotationid`
- `public.smtbtworkorderhdr.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbtworkorderhdr.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtworkorderhdr.ratezoneid` → `public.smtbmratezone.ratezoneid`
- `public.smtbtarrearinvoiceratedtl.arrearinvhdrid` → `public.smtbtarrearinvoicedtl.arrearinvhdrid`
- `public.smtbtarrearinvoiceratedtl.arrearinvbrhdrid` → `public.smtbtarrearinvoicehdr.arrearinvbrhdrid`
- `public.smtbtarrearinvoiceratedtl.invoicehdrid` → `public.smtbtinvoicehdr.invoicehdrid`
- `public.smtbtarrearinvoiceratedtl.wohdrid` → `public.smtbtworkorderhdr.wohdrid`
- `public.smtbtarrearinvoiceratedtl.wodtlid` → `public.smtbtworkorderdtl.wodtlid`
- `public.smtbtarrearinvoiceratedtl.resourceid` → `public.smtbmresource.resourceid`
- `public.smtbmsalaryhdeffdate.salaryheadid` → `public.smtbmsalaryhead.salaryheadid`
- `public.smtbtcustinquiry.inquiryid` → `public.smtbtinquiry.inquiryid`
- `public.smtbtcustinquiry.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtcustinquiry.empid` → `public.smtbmemployee.empid`
- `public.smtbtemployeebonuschildhistory.empid` → `public.smtbmemployee.empid`
- `public.smtbtemployeebonuschildhistory.wodtlid` → `public.smtbtworkorderdtl.wodtlid`
- `public.menupad.menuid` → `public.smtbmodule.menuid`
- `public.smtbtbranchinvoicedtl.invoicebrhdrid` → `public.smtbtbranchinvoice.invoicebrhdrid`
- `public.smtbtbranchinvoicedtl.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtbranchinvoicedtl.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbtbranchinvoicedtl.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtbranchinvoicedtl.wohdrid` → `public.smtbtworkorderhdr.wohdrid`
- `public.smtbtcustpaymenthdr.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbmemployeeprofile.empid` → `public.smtbmemployee.empid`
- `public.smtbmemployeeprofile.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbmemployeeprofile.deptid` → `public.smtbmdepartment.deptid`
- `public.smtbmemployeeprofile.designationid` → `public.smtbmdesignation.designationid`
- `public.smtbmemployeeprofile.gradeid` → `public.smtbmgradehdr.gradeid`
- `public.smtbmemployeeprofile.resourceid` → `public.smtbmresource.resourceid`
- `public.smtbgratebasisdtl.ratebasishdrid` → `public.smtbgratebasishdr.ratebasishdrid`
- `public.smtbgratebasisdtl.ratecardid` → `public.smtbmratecard.ratecardid`
- `public.smtbmprincipalrtamount.brlocid` → `public.smtbmbranch.brlocid`
- `public.dashboard_user_layout.user_id` → `public.smtbmusers.userid`
- `public.smtbmresource.resourcegroupprintid` → `public.smtbmresourcegroup.resourcegroupprintid`
- `public.smtbmresource.resourcenewid` → `public.smtbmresourcenew.resourceid`
- `public.smtbgformuladtl.formulahdrid` → `public.smtbgformulahdr.formulahdrid`
- `public.smtbgformuladtl.salaryheadid` → `public.smtbmsalaryhead.salaryheadid`
- `public.smtbmitemdefinition.makeid` → `public.smtbmmake.makeid`
- `public.smtbmitemdefinition.categoryid` → `public.smtbmcategory.categoryid`
- `public.smtbmitemdefinition.familyid` → `public.smtbmfamily.familyid`
- `public.smtbmitemdefinition.acheadid` → `public.smtbmachead.acheadid`
- `public.smtbtbdr.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtemployeebonuschild.empid` → `public.smtbmemployee.empid`
- `public.smtbtemployeebonuschild.wodtlid` → `public.smtbtworkorderdtl.wodtlid`
- `public.smtbmcustomerhistory.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbmcustomerhistory.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbmcustomerhistory.cityid` → `public.smtbmcity.cityid`
- `public.smtbminsurance.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbminsurance.empid` → `public.smtbmemployee.empid`
- `public.smtbminsurance.salaryheadid` → `public.smtbmsalaryhead.salaryheadid`
- `public.smtbtemployeeleavemasterhistory.leavemasterid` → `public.smtbtemployeeleavemaster.leavemasterid`
- `public.smtbtemployeeleavemasterhistory.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtemployeeleavemasterhistory.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbtemployeeleavemasterhistory.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtemployeefullfinalsalarydetail.fullfinalprocessid` → `public.smtbtemployeefullfinalsalary.fullfinalprocessid`
- `public.smtbtemployeefullfinalsalarydetail.bonusprocessid` → `public.smtbtemployeebonussalary.bonusprocessid`
- `public.smtbtemployeefullfinalsalarydetail.leaveprocessid` → `public.smtbtemployeeleavesalary.leaveprocessid`
- `public.smtbtemployeefullfinalsalarydetail.loanid` → `public.smtbtcashdetails.loanid`
- `public.smtbtemployeefullfinalsalarydetail.arrearid` → `public.smtbtarrears.arrearid`
- `public.smtbmmonthlyratehdr.stateid` → `public.smtbmstate.stateid`
- `public.smtbmmonthlyratehdr.resourceid` → `public.smtbmresource.resourceid`
- `public.smtbmmonthlyratehdr.ratezoneid` → `public.smtbmratezone.ratezoneid`
- `public.smtbmmonthlyratehdr.gradeid` → `public.smtbmgradehdr.gradeid`
- `public.smtbtemployeeleavesalarygeneral.empid` → `public.smtbmemployee.empid`
- `public.smtbtemployeeleavesalarygeneral.customer_id` → `public.smtbmcustomer.customerid`
- `public.smtbtemployeeleavesalarygeneral.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtemployeeleavesalarygeneral.companyid` → `public.smtbmcompany.companyid`
- `public.smtbtemployeeleavechildhistory.leavedetailid` → `public.smtbtemployeeleavechild.leavedetailid`
- `public.smtbtemployeeleavechildhistory.leavemasterid` → `public.smtbtemployeeleavemaster.leavemasterid`
- `public.smtbtemployeeleavechildhistory.empid` → `public.smtbmemployee.empid`
- `public.smtbtemployeeleavechildhistory.wodtlid` → `public.smtbtworkorderdtl.wodtlid`
- `public.smtbtuserpermbranch.userid` → `public.smtbmusers.userid`
- `public.smtbtuserpermbranch.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbmempsalheadhistorydtl.empid` → `public.smtbmemployee.empid`
- `public.smtbmempsalheadhistorydtl.gradeid` → `public.smtbmgradehdr.gradeid`
- `public.smtbmempsalheadhistorydtl.salaryheadid` → `public.smtbmsalaryhead.salaryheadid`
- `public.smtbmvendorpayheads.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtleavedetail.empid` → `public.smtbmemployee.empid`
- `public.smtbtleavedetail.leavetypeid` → `public.smtbgleavetype.leavetype_id`
- `public.smtbtpurchaseorderdtl_audit.podtlid` → `public.smtbtpurchaseorderdtl.podtlid`
- `public.smtbtpurchaseorderdtl_audit.pohdrid` → `public.smtbtpurchaseorderhdr.pohdrid`
- `public.smtbtpurchaseorderdtl_audit.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtpurchaseorderdtl_audit.resourceid` → `public.smtbmresource.resourceid`
- `public.smtbtpurchaseorderdtl_audit.ratecharthdrid` → `public.smtbmratecharthdr.ratecharthdrid`
- `public.smtbtpurchaseorderdtl_audit.attstatusid` → `public.smtbgattendancestatus.attstatusid`
- `public.smtbtconsolidateinvsequence.stateid` → `public.smtbmstate.stateid`
- `public.smtbtconsolidateinvsequence.finyearid` → `public.smtbgfinyear.finyearid`
- `public.smtbtarrearsdetailsummary.arrearid` → `public.smtbtarrears.arrearid`
- `public.smtbtarrearsdetailsummary.empid` → `public.smtbmemployee.empid`
- `public.smtbtarrearsdetailsummary.companyid` → `public.smtbmcompany.companyid`
- `public.smtbtleaveapplication.empid` → `public.smtbmemployee.empid`
- `public.smtbtleaveapplication.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtleaveapplication.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbmneftdetails.neftmasterid` → `public.smtbmneftmaster.neftmasterid`
- `public.smtbtsocietywef.societyid` → `public.smtbtsociety.societyid`
- `public.smtbtbulkinvoiceratedtl.invoicehdrid` → `public.smtbtinvoicehdr.invoicehdrid`
- `public.smtbtbulkinvoiceratedtl.invoicerefhdrid` → `public.smtbtbulkinvoicehdr.invoicerefhdrid`
- `public.smtbtbulkinvoiceratedtl.pohdrid` → `public.smtbtpurchaseorderhdr.pohdrid`
- `public.smtbtbulkinvoiceratedtl.podtlid` → `public.smtbtpurchaseorderdtl.podtlid`
- `public.smtbtbulkinvoiceratedtl.resourceid` → `public.smtbmresource.resourceid`
- `public.smtbtdeploymentdtl.deploymenthdrid` → `public.smtbtdeploymenthdr.deploymenthdrid`
- `public.smtbtdeploymentdtl.wohdrid` → `public.smtbtworkorderhdr.wohdrid`
- `public.smtbtdeploymentdtl.wodtlid` → `public.smtbtworkorderdtl.wodtlid`
- `public.smtbtdeploymentdtl.resourceid` → `public.smtbmresource.resourceid`
- `public.smtbtdeploymentdtl.shiftid` → `public.smtbmshift.shiftid`
- `public.smtbtdeploymentdtl.empid` → `public.smtbmemployee.empid`
- `public.smtbmrandtamount.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbgpayslipdetaildtl.payslipdtlhdrid` → `public.smtbgpayslipdetailhdr.payslipdtlhdrid`
- `public.smtbtbranchinvoiceratedtl.invoicehdrid` → `public.smtbtinvoicehdr.invoicehdrid`
- `public.smtbtbranchinvoiceratedtl.invoicebrhdrid` → `public.smtbtbranchinvoice.invoicebrhdrid`
- `public.smtbtbranchinvoiceratedtl.wohdrid` → `public.smtbtworkorderhdr.wohdrid`
- `public.smtbtbranchinvoiceratedtl.wodtlid` → `public.smtbtworkorderdtl.wodtlid`
- `public.smtbtbranchinvoiceratedtl.resourceid` → `public.smtbmresource.resourceid`
- `public.smtbmemployeedtl.empid` → `public.smtbmemployee.empid`
- `public.smtbmemployeedtl.cityid` → `public.smtbmcity.cityid`
- `public.smtbmemployeepvdetails.empid` → `public.smtbmemployee.empid`
- `public.smtbmcustlocgroup.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtbulkinvoicedtl.invoicerefhdrid` → `public.smtbtbulkinvoicehdr.invoicerefhdrid`
- `public.smtbtbulkinvoicedtl.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbtbulkinvoicedtl.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtbulkinvoicedtl.pohdrid` → `public.smtbtpurchaseorderhdr.pohdrid`
- `public.smtbthradedemplisthdr.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtarrearinvoicedtl.arrearinvbrhdrid` → `public.smtbtarrearinvoicehdr.arrearinvbrhdrid`
- `public.smtbtarrearinvoicedtl.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtarrearinvoicedtl.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbtarrearinvoicedtl.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtarrearinvoicedtl.wohdrid` → `public.smtbtworkorderhdr.wohdrid`
- `public.smtbminvoiceconsogrphdr.stateid` → `public.smtbmstate.stateid`
- `public.smtbminvoiceconsogrphdr.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbalertoutbox.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtsdhdr.vendorid` → `public.smtbmvendor.vendorid`
- `public.smtbtsdhdr.categoryid` → `public.smtbmcategory.categoryid`
- `public.smtbtsdhdr.bankbrid` → `public.smtbmbank.bankbrid`
- `public.smtbtsdhdr.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtsdhdr.typeid` → `public.smtbmtype.typeid`
- `public.smtbgpayslipheaderdtl.paysliphdrid` → `public.smtbgpayslipheaderhdr.paysliphdrid`
- `public.getemp.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtconsomst.stateid` → `public.smtbmstate.stateid`
- `public.smtbtconsomst.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbmcityduplicate.cityid` → `public.smtbmcity.cityid`
- `public.smtbmcityduplicate.stateid` → `public.smtbmstate.stateid`
- `public.smtbtemployeebonusmaster.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtemployeebonusmaster.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbtemployeebonusmaster.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtposting.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtposting.wohdrid` → `public.smtbtworkorderhdr.wohdrid`
- `public.closedcontract.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtloandetails.empid` → `public.smtbmemployee.empid`
- `public.smtbtloandetails.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtloandetails.bankid` → `public.smtbmbank.bankbrid`
- `public.smtbtloandetails.salaryheadid` → `public.smtbmsalaryhead.salaryheadid`
- `public.dashboard_fact_outstanding_branch.branch_id` → `public.smtbmbranch.brlocid`
- `public.smtbgempwisegrouphdr.empid` → `public.smtbmemployee.empid`
- `public.smtbmarrearssalary.arrears_id` → `public.smtbtarrears.arrearid`
- `public.smtbmarrearssalary.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbmarrearssalary.resourceid` → `public.smtbmresource.resourceid`
- `public.smtbgwagereportformat.bankid` → `public.smtbmbank.bankbrid`
- `public.smtbtcustinvpaymenthdr.finyearid` → `public.smtbgfinyear.finyearid`
- `public.smtbtcustinvpaymenthdr.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbtcustinvpaymenthdr.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtcustinvpaymenthdr.bankbrid` → `public.smtbmbank.bankbrid`
- `public.smtbtcustinvpaymenthdr.brlocid` → `public.smtbmbranch.brlocid`
- `public.accountno.branchid` → `public.smtbmbranch.brlocid`
- `public.accountno.bankbrid` → `public.smtbmbank.bankbrid`
- `public.smtbtemployeeleavemaster.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtemployeeleavemaster.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbtemployeeleavemaster.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtemdhdr.bankbrid` → `public.smtbmbank.bankbrid`
- `public.smtbtemdhdr.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtemdhdr.typeid` → `public.smtbmtype.typeid`
- `public.smtbmclientexcemption.customer_id` → `public.smtbmcustomer.customerid`
- `public.smtbmclientexcemption.salaryheadid` → `public.smtbmsalaryhead.salaryheadid`
- `public.smtbmemployee_bankdetails.bankbrid` → `public.smtbmbank.bankbrid`
- `public.smtbmemployee_bankdetails.bankcategoryid` → `public.smtbmbankcategory.bankcategoryid`
- `public.rptprlguardsalarydetail.wodtlid` → `public.smtbtworkorderdtl.wodtlid`
- `public.smtbgjobrolepermission.jobroleid` → `public.smtbmjobrole.jobroleid`
- `public.smtbgjobrolepermission.menuid` → `public.smtbmodule.menuid`
- `public.auditlogs.user_id` → `public.smtbmusers.userid`
- `public.smtbtemployeeleavechild.leavemasterid` → `public.smtbtemployeeleavemaster.leavemasterid`
- `public.smtbtemployeeleavechild.empid` → `public.smtbmemployee.empid`
- `public.smtbtemployeeleavechild.wodtlid` → `public.smtbtworkorderdtl.wodtlid`
- `public.smtbtcreditnote.emp_id` → `public.smtbmemployee.empid`
- `public.smtbtcreditnote.leaveprocessid` → `public.smtbtemployeeleavesalary.leaveprocessid`
- `public.smtbtcreditnote.bonusprocessid` → `public.smtbtemployeebonussalary.bonusprocessid`
- `public.smtbtcreditnote.fullfinalprocessid` → `public.smtbtemployeefullfinalsalary.fullfinalprocessid`
- `public.smtbtcreditnote.arrearprocessid` → `public.smtbtemployeearrearsalary.arrearprocessid`
- `public.smtbtemployeebonuschild1.empid` → `public.smtbmemployee.empid`
- `public.smtbtemployeebonuschild1.wodtlid` → `public.smtbtworkorderdtl.wodtlid`
- `public.smtbmbranchholidayhdr.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbmbranchholidayhdr.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbmbranchholidayhdr.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtemployeebonussalarygeneral.empid` → `public.smtbmemployee.empid`
- `public.smtbtemployeebonussalarygeneral.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtemployeebonussalarygeneral.branchid` → `public.smtbmbranch.brlocid`
- `public.smtbtemployeebonussalarygeneral.companyid` → `public.smtbmcompany.companyid`
- `public.smtbtvendortransactionhdr.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtvendortransactionhdr.userid` → `public.smtbmusers.userid`
- `public.smtbtvendortransactionhdr.finyearid` → `public.smtbgfinyear.finyearid`
- `public.smtbm_taglinemast.companyid` → `public.smtbmcompany.companyid`
- `public.smtbmemployeeprofiletemp.profileid` → `public.smtbmemployeeprofile.profileid`
- `public.smtbmemployeeprofiletemp.empid` → `public.smtbmemployee.empid`
- `public.smtbmemployeeprofiletemp.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbmemployeeprofiletemp.deptid` → `public.smtbmdepartment.deptid`
- `public.smtbmemployeeprofiletemp.designationid` → `public.smtbmdesignation.designationid`
- `public.smtbmemployeeprofiletemp.gradeid` → `public.smtbmgradehdr.gradeid`
- `public.smtbmemployeeprofiletemp.resourceid` → `public.smtbmresource.resourceid`
- `public.smtbtholdpaydtl.holdpayhdrid` → `public.smtbtholdpayhdr.holdpayhdrid`
- `public.smtbtholdpaydtl.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtholdpaydtl.leaveprocessid` → `public.smtbtemployeeleavesalary.leaveprocessid`
- `public.smtbtholdpaydtl.bonusprocessid` → `public.smtbtemployeebonussalary.bonusprocessid`
- `public.smtbtholdpaydtl.fullfinalprocessid` → `public.smtbtemployeefullfinalsalary.fullfinalprocessid`
- `public.wild.empid` → `public.smtbmemployee.empid`
- `public.smtbtquotationdtl.quotationid` → `public.smtbtquotation.quotationid`
- `public.smtbtquotationdtl.monthlyratecardhdrid` → `public.smtbmmonthlyratehdr.monthlyratecardhdrid`
- `public.temptableuanno.branchid` → `public.smtbmbranch.brlocid`
- `public.smtbtpurchaseorderratedtl_audit.poratedtlid` → `public.smtbtpurchaseorderratedtl.poratedtlid`
- `public.smtbtpurchaseorderratedtl_audit.podtlid` → `public.smtbtpurchaseorderdtl.podtlid`
- `public.smtbtpurchaseorderratedtl_audit.pohdrid` → `public.smtbtpurchaseorderhdr.pohdrid`
- `public.smtbtpurchaseorderratedtl_audit.ratecharthdrid` → `public.smtbmratecharthdr.ratecharthdrid`
- `public.smtbtpurchaseorderratedtl_audit.ratecardid` → `public.smtbmratecard.ratecardid`
- `public.smtbtemployeebonussalary.empid` → `public.smtbmemployee.empid`
- `public.smtbtemployeebonussalary.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtemployeebonussalary.branchid` → `public.smtbmbranch.brlocid`
- `public.smtbtemployeebonussalary.companyid` → `public.smtbmcompany.companyid`
- `public.smtbtcustinvpaydtl.invpayhdrid` → `public.smtbtcustinvpaymenthdr.invpayhdrid`
- `public.smtbtcustinvpaydtl.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtcustinvpaydtl.invoicehdrid` → `public.smtbtinvoicehdr.invoicehdrid`
- `public.smtbtcustinvpaydtl.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbmbankcategory.bankbrid` → `public.smtbmbank.bankbrid`
- `public.smtbtcustsalarypaymentdtl.custpaymenthdrid` → `public.smtbtcustpaymenthdr.custpaymenthdrid`
- `public.smtbtcustsalarypaymentdtl.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbglocktransation.transid` → `public.smtbgactiveuser.transid`
- `public.smtbglocktransation.userid` → `public.smtbmusers.userid`
- `public.smtbgactiveuser.empid` → `public.smtbmemployee.empid`
- `public.smtbmbank.cityid` → `public.smtbmcity.cityid`
- `public.esicsubcode.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtmonthlysummary_staging.empid` → `public.smtbmemployee.empid`
- `public.smtbtmonthlysummary_staging.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtmonthlysummary_staging.gradeid` → `public.smtbmgradehdr.gradeid`
- `public.smtbtmonthlysummary_staging.departmentid` → `public.smtbmdepartment.deptid`
- `public.smtbtmonthlysummary_staging.designationid` → `public.smtbmdesignation.designationid`
- `public.smtbtmonthlysummary_staging.companyid` → `public.smtbmcompany.companyid`
- `public.smtbtmonthlysummary_staging.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtmonthlysummary_staging.resourceid` → `public.smtbmresource.resourceid`
- `public.smtbtmonthlysummary_staging.wodtlid` → `public.smtbtworkorderdtl.wodtlid`
- `public.smtbtmonthlysummary_staging.processhdrid` → `public.smtbtcommonprocesshdr.processhdrid`
- `public.smtbtarrears.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtarrears.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbtarrears.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtarrears.resourceid` → `public.smtbmresource.resourceid`
- `public.smtbtarrears.empid` → `public.smtbmemployee.empid`
- `public.smtbtarrears.companyid` → `public.smtbmcompany.companyid`
- `public.smtbtpurchaseorderhdr.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtpurchaseorderhdr.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbtpurchaseorderhdr.ratezoneid` → `public.smtbmratezone.ratezoneid`
- `public.smtbmemployee_audit.designationid` → `public.smtbmdesignation.designationid`
- `public.smtbmemployee_audit.shiftid` → `public.smtbmshift.shiftid`
- `public.smtbmemployee_audit.gradeid` → `public.smtbmgradehdr.gradeid`
- `public.smtbmemployee_audit.branchid` → `public.smtbmbranch.brlocid`
- `public.smtbmemployee_audit.departmentid` → `public.smtbmdepartment.deptid`
- `public.smtbmemployee_audit.bankbrid` → `public.smtbmbank.bankbrid`
- `public.smtbmemployee_audit.resourceid` → `public.smtbmresource.resourceid`
- `public.smtbmemployee_audit.resourcegroupprintid` → `public.smtbmresourcegroup.resourcegroupprintid`
- `public.smtbmemployee_audit.bankcategoryid` → `public.smtbmbankcategory.bankcategoryid`
- `public.smtbmemployee_audit.empid` → `public.smtbmemployee.empid`
- `public.smtbmcustomer_audit.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbmcustomer_audit.industryid` → `public.smtbmindustry.industryid`
- `public.smtbmcustomer_audit.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbmcustomer_audit.cityid` → `public.smtbmcity.cityid`
- `public.smtbmcustomer_audit.catagoryid` → `public.smtbmcustcatagory.catagoryid`
- `public.smtbthradedemplistdtl.transhdrid` → `public.smtbthradedemplisthdr.transhdrid`
- `public.smtbthradedemplistdtl.empid` → `public.smtbmemployee.empid`
- `public.smtbtemployeearrearsalary.empid` → `public.smtbmemployee.empid`
- `public.smtbgempwisegroupdtl.empwisegrouphdrid` → `public.smtbgempwisegrouphdr.empwisegrouphdrid`
- `public.smtbtarrearsdetail.arrearid` → `public.smtbtarrears.arrearid`
- `public.smtbtarrearsdetail.ratecardid` → `public.smtbmratecard.ratecardid`
- `public.smtbtarrearsdetail.companyid` → `public.smtbmcompany.companyid`
- `public.smtbtarrearsdetail.resourceid` → `public.smtbmresource.resourceid`
- `public.tempsmtbtdailyattendance.brlocid` → `public.smtbmbranch.brlocid`
- `public.tempsmtbtdailyattendance.empid` → `public.smtbmemployee.empid`
- `public.tempsmtbtdailyattendance.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.tempsmtbtdailyattendance.wohdrid` → `public.smtbtworkorderhdr.wohdrid`
- `public.tempsmtbtdailyattendance.wodtlid` → `public.smtbtworkorderdtl.wodtlid`
- `public.tempsmtbtdailyattendance.resourceid` → `public.smtbmresource.resourceid`
- `public.tempsmtbtdailyattendance.attstatusid` → `public.smtbgattendancestatus.attstatusid`
- `public.tempsmtbtdailyattendance.shiftid` → `public.smtbmshift.shiftid`
- `public.tempsmtbtdailyattendance.custshiftid` → `public.smtbmcustomershift.custshiftid`
- `public.user_activity_log.user_id` → `public.smtbmusers.userid`
- `public.smtbmemployeegroupdtl.empgrouphdrid` → `public.smtbmemployeegrouphdr.empgrouphdrid`
- `public.smtbmemployeegroupdtl.empid` → `public.smtbmemployee.empid`
- `public.empaccno.empid` → `public.smtbmemployee.empid`
- `public.empaccno.bankbrid` → `public.smtbmbank.bankbrid`
- `public.smtbtmiscsalaryhdr.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtmiscsalaryhdr.empid` → `public.smtbmemployee.empid`
- `public.smtbtmiscsalaryhdr.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtmiscsalaryhdr.resourceid` → `public.smtbmresource.resourceid`
- `public.smtbtmiscsalaryhdr.vendorid` → `public.smtbmvendor.vendorid`
- `public.smtbusermodule.menuid` → `public.smtbmodule.menuid`
- `public.smtbtagreementhdr.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtagreementhdr.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbtagreementhdr.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtusedrecovery.brlocid` → `public.smtbmbranch.brlocid`
- `public.esicnopf.branchid` → `public.smtbmbranch.brlocid`
- `public.smtbtvendortransactiondtl.vendorid` → `public.smtbmvendor.vendorid`
- `public.smtbtvendortransactiondtl.vendorpayheadid` → `public.smtbmvendorpayheads.vpayheadid`
- `public.temprelf.empid` → `public.smtbmemployee.empid`
- `public.smtbmcustomer.industryid` → `public.smtbmindustry.industryid`
- `public.smtbmcustomer.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbmcustomer.cityid` → `public.smtbmcity.cityid`
- `public.smtbmcustomer.catagoryid` → `public.smtbmcustcatagory.catagoryid`
- `public.smtbmcustomershift.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbmcustomershift.attstatusid` → `public.smtbgattendancestatus.attstatusid`
- `public.smtbmptaxslabdtl.ptaxhdrid` → `public.smtbmptaxslabhdr.ptaxhdrid`
- `public.smtbtmonthlysummary.empid` → `public.smtbmemployee.empid`
- `public.smtbtmonthlysummary.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtmonthlysummary.gradeid` → `public.smtbmgradehdr.gradeid`
- `public.smtbtmonthlysummary.departmentid` → `public.smtbmdepartment.deptid`
- `public.smtbtmonthlysummary.designationid` → `public.smtbmdesignation.designationid`
- `public.smtbtmonthlysummary.companyid` → `public.smtbmcompany.companyid`
- `public.smtbtmonthlysummary.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtmonthlysummary.resourceid` → `public.smtbmresource.resourceid`
- `public.smtbtmonthlysummary.wodtlid` → `public.smtbtworkorderdtl.wodtlid`
- `public.smtbtmonthlysummary.processhdrid` → `public.smtbtcommonprocesshdr.processhdrid`
- `public.smtbtpurchaseorderotherdtl.podtlid` → `public.smtbtpurchaseorderdtl.podtlid`
- `public.smtbtpurchaseorderotherdtl.invoicerefhdrid` → `public.smtbtbulkinvoicehdr.invoicerefhdrid`
- `public.smtbmratecard.ratebasishdrid` → `public.smtbgratebasishdr.ratebasishdrid`
- `public.smtbmratecard.salaryheadid` → `public.smtbmsalaryhead.salaryheadid`
- `public.smtbtinvoicehdr.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtinvoicehdr.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbtinvoicehdr.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbmemployeegrouphdr.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbmcustbrloc.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbmcustbrloc.custlocgroupid` → `public.smtbmcustlocgroup.custlocgroupid`
- `public.smtbmcustbrloc.cityid` → `public.smtbmcity.cityid`
- `public.smtbmcustbrloc.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbmcustbrloc.leave_slab_id` → `public.smtbmleaveslab_master.leave_slab_id`
- `public.smtbmcustbrloc.neftmasterid` → `public.smtbmneftmaster.neftmasterid`
- `public.smtbtcashdetails.empid` → `public.smtbmemployee.empid`
- `public.smtbtcashdetails.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtcashdetails.bankid` → `public.smtbmbank.bankbrid`
- `public.smtbtcashdetails.salaryheadid` → `public.smtbmsalaryhead.salaryheadid`
- `public.smtbmratezone.stateid` → `public.smtbmstate.stateid`
- `public.smtbminvoiceconsogrpdtl.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbmusers.empid` → `public.smtbmemployee.empid`
- `public.smtbmusers.jobroleid` → `public.smtbmjobrole.jobroleid`
- `public.smtbmarrearssummary.arrears_id` → `public.smtbtarrears.arrearid`
- `public.smtbmarrearssummary.empid` → `public.smtbmemployee.empid`
- `public.smtbmcity.stateid` → `public.smtbmstate.stateid`
- `public.smtbtquotationratedtl.quotationdtlid` → `public.smtbtquotationdtl.quotationdtlid`
- `public.smtbtquotationratedtl.quotationid` → `public.smtbtquotation.quotationid`
- `public.smtbtquotationratedtl.monthlyratecardhdrid` → `public.smtbmmonthlyratehdr.monthlyratecardhdrid`
- `public.smtbtquotationratedtl.ratecardid` → `public.smtbmratecard.ratecardid`
- `public.smtbtconsolidateinvno.stateid` → `public.smtbmstate.stateid`
- `public.smtbtconsolidateinvno.finyearid` → `public.smtbgfinyear.finyearid`
- `public.smtbtemployeeleavesummaryhistory.leaveprocessid` → `public.smtbtemployeeleavesalary.leaveprocessid`
- `public.smtbtemployeeleavesummaryhistory.leavemasterid` → `public.smtbtemployeeleavemaster.leavemasterid`
- `public.smtbtemployeeleavesummaryhistory.empid` → `public.smtbmemployee.empid`
- `public.smtbtemployeeleavesummary.leavemasterid` → `public.smtbtemployeeleavemaster.leavemasterid`
- `public.smtbtemployeeleavesummary.empid` → `public.smtbmemployee.empid`
- `public.regional_settings.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbmcustomershifttemp.custshiftid` → `public.smtbmcustomershift.custshiftid`
- `public.smtbmcustomershifttemp.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbmemployee.designationid` → `public.smtbmdesignation.designationid`
- `public.smtbmemployee.shiftid` → `public.smtbmshift.shiftid`
- `public.smtbmemployee.gradeid` → `public.smtbmgradehdr.gradeid`
- `public.smtbmemployee.branchid` → `public.smtbmbranch.brlocid`
- `public.smtbmemployee.departmentid` → `public.smtbmdepartment.deptid`
- `public.smtbmemployee.bankbrid` → `public.smtbmbank.bankbrid`
- `public.smtbmemployee.resourceid` → `public.smtbmresource.resourceid`
- `public.smtbmemployee.resourcegroupprintid` → `public.smtbmresourcegroup.resourcegroupprintid`
- `public.smtbmemployee.bankcategoryid` → `public.smtbmbankcategory.bankcategoryid`
- `public.smtbmemployee_old.empid` → `public.smtbmemployee.empid`
- `public.smtbmemployee_old.designationid` → `public.smtbmdesignation.designationid`
- `public.smtbmemployee_old.shiftid` → `public.smtbmshift.shiftid`
- `public.smtbmemployee_old.gradeid` → `public.smtbmgradehdr.gradeid`
- `public.smtbmemployee_old.branchid` → `public.smtbmbranch.brlocid`
- `public.smtbmemployee_old.departmentid` → `public.smtbmdepartment.deptid`
- `public.smtbmemployee_old.bankbrid` → `public.smtbmbank.bankbrid`
- `public.smtbmemployee_old.resourceid` → `public.smtbmresource.resourceid`
- `public.smtbmemployee_old.resourcegroupprintid` → `public.smtbmresourcegroup.resourcegroupprintid`
- `public.smtbmemployee_old.bankcategoryid` → `public.smtbmbankcategory.bankcategoryid`
- `public.smtbtadvancedetail.advanceid` → `public.smtbtadvance.advanceid`
- `public.smtbtadvancedetail.empid` → `public.smtbmemployee.empid`
- `public.smtbtadvancedetail.salaryheadid` → `public.smtbmsalaryhead.salaryheadid`
- `public.smtbtadvance.empid` → `public.smtbmemployee.empid`
- `public.smtbtadvance.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtsociety.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtsociety.empid` → `public.smtbmemployee.empid`
- `public.smtbtsociety.salaryheadid` → `public.smtbmsalaryhead.salaryheadid`
- `public.smtbtbulkinvoicedtldelete.finyearid` → `public.smtbgfinyear.finyearid`
- `public.smtbtbulkinvoicedtldelete.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbmptaxslabhdr.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbmptaxslabhdr.salaryheadid` → `public.smtbmsalaryhead.salaryheadid`
- `public.smtbmptaxslabhdr.stateid` → `public.smtbmstate.stateid`
- `public.smtbmptaxslabhdr.typeid` → `public.smtbmtype.typeid`
- `public.smtbtarrearmonthlysummary.empid` → `public.smtbmemployee.empid`
- `public.smtbtarrearmonthlysummary.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtarrearmonthlysummary.companyid` → `public.smtbmcompany.companyid`
- `public.smtbtarrearmonthlysummary.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtarrearmonthlysummary.resourceid` → `public.smtbmresource.resourceid`
- `public.smtbtarrearmonthlysummary.wodtlid` → `public.smtbtworkorderdtl.wodtlid`
- `public.smtbtpurchaseorderratedtl.podtlid` → `public.smtbtpurchaseorderdtl.podtlid`
- `public.smtbtpurchaseorderratedtl.pohdrid` → `public.smtbtpurchaseorderhdr.pohdrid`
- `public.smtbtpurchaseorderratedtl.ratecharthdrid` → `public.smtbmratecharthdr.ratecharthdrid`
- `public.smtbtpurchaseorderratedtl.ratecardid` → `public.smtbmratecard.ratecardid`
- `public.temp_day7.empid` → `public.smtbmemployee.empid`
- `public.temp_day7.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtbulkinvoicegstdetails.invoicehdrid` → `public.smtbtinvoicehdr.invoicehdrid`
- `public.smtbtbulkinvoicegstdetails.invoicerefhdrid` → `public.smtbtbulkinvoicehdr.invoicerefhdrid`
- `public.smtbtbulkinvoicegstdetails.serviceid` → `public.smtbmservices.serviceid`
- `public.custlot.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbmfamily.categoryid` → `public.smtbmcategory.categoryid`
- `public.smtbtquotation.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtquotation.inquiryid` → `public.smtbtinquiry.inquiryid`
- `public.smtbtquotation.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbtquotation.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtquotation.stateid` → `public.smtbmstate.stateid`
- `public.smtbtquotation.ratezoneid` → `public.smtbmratezone.ratezoneid`
- `public.smtbtbankguaranty.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbtbankguaranty.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtbankguaranty.wodtlid` → `public.smtbtworkorderdtl.wodtlid`
- `public.smtbtbankguaranty.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtsalarypaymenthdr.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtsalarypaymenthdr.userid` → `public.smtbmusers.userid`
- `public.smtbtsalarypaymenthdr.bankbrid` → `public.smtbmbank.bankbrid`
- `public.smtbtemployeebonussummary.empid` → `public.smtbmemployee.empid`
- `public.smtbtemployeefullfinalsalary.empid` → `public.smtbmemployee.empid`
- `public.smtbtagreementdtl.agreementhdrid` → `public.smtbtagreementhdr.agreementhdrid`
- `public.smtbtagreementdtl.wohdrid` → `public.smtbtworkorderhdr.wohdrid`
- `public.smtbmresourcenew.resourcegroupid` → `public.smtbmresourcegroupnew.resourcegroupid`
- `public.smtbmresourcenew.serviceid` → `public.smtbmservices.serviceid`
- `public.smtbtbulkinvoicehdr.finyearid` → `public.smtbgfinyear.finyearid`
- `public.smtbmodule_backup.menuid` → `public.smtbmodule.menuid`
- `public.smtbmcustlocgroupdtl.custlocgrouphdrid` → `public.smtbmcustlocgrouphdr.custlocgrouphdrid`
- `public.smtbmcustlocgroupdtl.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.dashboard_fact_aging_customer.branch_id` → `public.smtbmbranch.brlocid`
- `public.dashboard_fact_aging_customer.customer_id` → `public.smtbmcustomer.customerid`
- `public.smtbtloanpayment.loanid` → `public.smtbtcashdetails.loanid`
- `public.smtbtloanpayment.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtloanpayment.resourceid` → `public.smtbmresource.resourceid`
- `public.smtbmshift.attstatusid` → `public.smtbgattendancestatus.attstatusid`
- `public.dashboard_fact_billing_monthly.branch_id` → `public.smtbmbranch.brlocid`
- `public.dashboard_fact_billing_monthly.customer_id` → `public.smtbmcustomer.customerid`
- `public.dashboard_fact_billing_monthly.state_id` → `public.smtbmstate.stateid`
- `public.smtbtemployeebonusmasterhistory.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtemployeebonusmasterhistory.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbtemployeebonusmasterhistory.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbguseraccesspermission.menuid` → `public.smtbmodule.menuid`
- `public.smtbguseraccesspermission.userid` → `public.smtbmusers.userid`
- `public.smtbtpaymentreturndetails.leaveprocessid` → `public.smtbtemployeeleavesalary.leaveprocessid`
- `public.smtbtpaymentreturndetails.bonusprocessid` → `public.smtbtemployeebonussalary.bonusprocessid`
- `public.smtbtpaymentreturndetails.fullfinalprocessid` → `public.smtbtemployeefullfinalsalary.fullfinalprocessid`
- `public.smtbtpaymentreturndetails.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtpaymentreturndetails.bankbrid` → `public.smtbmbank.bankbrid`
- `public.recovery.salaryheadid` → `public.smtbmsalaryhead.salaryheadid`
- `public.recovery.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtcommonprocesshdr.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtworkorderdtl.wohdrid` → `public.smtbtworkorderhdr.wohdrid`
- `public.smtbtworkorderdtl.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtworkorderdtl.monthlyratecardhdrid` → `public.smtbmmonthlyratehdr.monthlyratecardhdrid`
- `public.smtbtworkorderdtl.resourceid` → `public.smtbmresource.resourceid`
- `public.smtbtworkorderdtl.formulahdrid` → `public.smtbgformulahdr.formulahdrid`
- `public.smtbtworkorderratedtl.wodtlid` → `public.smtbtworkorderdtl.wodtlid`
- `public.smtbtworkorderratedtl.wohdrid` → `public.smtbtworkorderhdr.wohdrid`
- `public.smtbtworkorderratedtl.monthlyratecardhdrid` → `public.smtbmmonthlyratehdr.monthlyratecardhdrid`
- `public.smtbtworkorderratedtl.ratecardid` → `public.smtbmratecard.ratecardid`
- `public.smtbmratechartdtl.ratecharthdrid` → `public.smtbmratecharthdr.ratecharthdrid`
- `public.smtbmratechartdtl.ratecardid` → `public.smtbmratecard.ratecardid`
- `public.smtbmratechartdtl.ratebasishdrid` → `public.smtbgratebasishdr.ratebasishdrid`
- `public.smtbmgradedtl.gradeid` → `public.smtbmgradehdr.gradeid`
- `public.smtbmgradedtl.salaryheadid` → `public.smtbmsalaryhead.salaryheadid`
- `public.dashboard_fact_receipts_monthly.branch_id` → `public.smtbmbranch.brlocid`
- `public.dashboard_fact_receipts_monthly.customer_id` → `public.smtbmcustomer.customerid`
- `public.dashboard_fact_receipts_monthly.state_id` → `public.smtbmstate.stateid`
- `public.smtbtemployeegratuitysalary.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbtemployeegratuitysalary.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtemployeegratuitysalary.empid` → `public.smtbmemployee.empid`
- `public.smtbtinvoicedtl.invoicehdrid` → `public.smtbtinvoicehdr.invoicehdrid`
- `public.smtbtinvoicedtl.wohdrid` → `public.smtbtworkorderhdr.wohdrid`
- `public.smtbtinvoicedtl.wodtlid` → `public.smtbtworkorderdtl.wodtlid`
- `public.smtbtinvoicedtl.resourceid` → `public.smtbmresource.resourceid`
- `public.smtbmsalaryhead.gradeid` → `public.smtbmgradehdr.gradeid`
- `public.smtbtbulkinvoiceotherratedtl.invoicedtlid` → `public.smtbtinvoicedtl.invoicedtlid`
- `public.smtbtbulkinvoiceotherratedtl.invoicehdrid` → `public.smtbtinvoicehdr.invoicehdrid`
- `public.smtbtbulkinvoiceotherratedtl.invoicerefhdrid` → `public.smtbtbulkinvoicehdr.invoicerefhdrid`
- `public.smtbtbulkinvoiceotherratedtl.ratecardid` → `public.smtbmratecard.ratecardid`
- `public.smtbtmiscsalarydtl.miscsalaryid` → `public.smtbtmiscsalaryhdr.miscsalaryid`
- `public.smtbtmiscsalarydtl.salaryheadid` → `public.smtbmsalaryhead.salaryheadid`
- `public.smtbtmiscsalarydtl.empid` → `public.smtbmemployee.empid`
- `public.smtbtmiscsalarydtl.vpayheadid` → `public.smtbmvendorpayheads.vpayheadid`
- `public.smtbgreportformat.paysliphdrid` → `public.smtbgpayslipheaderhdr.paysliphdrid`
- `public.smtbgreportformat.payslipdtlhdrid` → `public.smtbgpayslipdetailhdr.payslipdtlhdrid`
- `public.smtbtholdpayhdr.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtholdpayhdr.customerid` → `public.smtbmcustomer.customerid`
- `public.smtbtholdpayhdr.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbtholdpayhdr.resourceid` → `public.smtbmresource.resourceid`
- `public.smtbtholdpayhdr.bankid` → `public.smtbmbank.bankbrid`
- `public.smtbmbranchholidaydtl.brholidayhdrid` → `public.smtbmbranchholidayhdr.brholidayhdrid`
- `public.smtbmbranchholidaydtl.holidayid` → `public.smtbmholiday.holidayid`
- `public.smtbmvendor.cityid` → `public.smtbmcity.cityid`
- `public.smtbmvendor.brlocid` → `public.smtbmbranch.brlocid`
- `public.smtbtbulkinvoiceotherdatadtl.invoicerefhdrid` → `public.smtbtbulkinvoicehdr.invoicerefhdrid`
- `public.smtbtbulkinvoiceotherdatadtl.pohdrid` → `public.smtbtpurchaseorderhdr.pohdrid`
- `public.smtbtbulkinvoiceotherdatadtl.podtlid` → `public.smtbtpurchaseorderdtl.podtlid`
- `public.smtbtbulkinvoiceotherdatadtl.custbrlocid` → `public.smtbmcustbrloc.custbrlocid`
- `public.smtbmgst.serviceid` → `public.smtbmservices.serviceid`

## All tables, ranked

| Score | Table | Rows (est.) | Measures | Dates | Groupings | Notes |
|---:|---|---:|---:|---:|---:|---|
| 268.4 | `public.smtbmbranch` | 162 | 0 | 9 | 10 | rows≈162, writes=0, reads=0, joins=88 |
| 225.1 | `public.smtbmemployee` | 349,421 | 5 | 25 | 2 | rows≈349,421, writes=0, reads=0, joins=70; has measures and a date column (possible fact table) |
| 187.2 | `public.smtbmcustbrloc` | 38,786 | 6 | 2 | 6 | rows≈38,786, writes=0, reads=0, joins=58; has measures and a date column (possible fact table) |
| 132.2 | `public.smtbmcustomer` | 12,513 | 1 | 2 | 3 | rows≈12,513, writes=0, reads=0, joins=40; has measures and a date column (possible fact table) |
| 99.6 | `public.smtbmresource` | 1,932 | 0 | 2 | 5 | rows≈1,932, writes=0, reads=0, joins=31 |
| 73.3 | `public.smtbtworkorderdtl` | 4,397 | 14 | 0 | 0 | rows≈4,397, writes=0, reads=0, joins=22 |
| 67.8 | `public.smtbtworkorderhdr` | 2,603 | 3 | 8 | 5 | rows≈2,603, writes=0, reads=0, joins=19; has measures and a date column (possible fact table) |
| 67.6 | `public.smtbmbank` | 63,370 | 2 | 2 | 4 | rows≈63,370, writes=0, reads=0, joins=18; has measures and a date column (possible fact table) |
| 59.0 | `public.smtbmsalaryhead` | 96 | 3 | 2 | 6 | rows≈96, writes=0, reads=0, joins=17; has measures and a date column (possible fact table) |
| 51.9 | `public.smtbtarrears` | 28,769 | 1 | 5 | 2 | rows≈28,769, writes=0, reads=0, joins=13; has measures and a date column (possible fact table) |
| 51.2 | `public.smtbmstate` | 39 | 0 | 2 | 0 | rows≈39, writes=0, reads=0, joins=16 |
| 48.0 | `public.smtbmcompany` | 9 | 1 | 2 | 0 | rows≈9, writes=0, reads=0, joins=14; has measures and a date column (possible fact table) |
| 48.0 | `public.smtbtpurchaseorderdtl` | 307,082 | 16 | 17 | 7 | rows≈307,082, writes=0, reads=0, joins=11; has measures and a date column (possible fact table) |
| 47.7 | `public.smtbmgradehdr` | 211 | 2 | 2 | 4 | rows≈211, writes=0, reads=0, joins=13; has measures and a date column (possible fact table) |
| 47.7 | `public.smtbtmonthlysummary` | 6,807,827 | 150 | 4 | 33 | rows≈6,807,827, writes=0, reads=0, joins=10; has measures and a date column (possible fact table) |
| 45.0 | `public.smtbmcity` | 1,039 | 0 | 2 | 4 | rows≈1,039, writes=0, reads=0, joins=13 |
| 44.4 | `public.smtbmratecard` | 156 | 1 | 2 | 5 | rows≈156, writes=0, reads=0, joins=12; has measures and a date column (possible fact table) |
| 44.0 | `public.smtbtemployeeleavesalary` | 97,765 | 32 | 5 | 5 | rows≈97,765, writes=0, reads=0, joins=10; has measures and a date column (possible fact table) |
| 43.8 | `public.smtbtemployeebonussalary` | 76,193 | 68 | 5 | 5 | rows≈76,193, writes=0, reads=0, joins=10; has measures and a date column (possible fact table) |
| 42.8 | `public.smtbtdailyattendance` | 78,013,328 | 0 | 6 | 1 | rows≈78,013,328, writes=0, reads=0, joins=9 |
| 41.7 | `public.smtbmusers` | 745 | 0 | 3 | 2 | rows≈745, writes=0, reads=0, joins=12 |
| 38.4 | `public.smtbtpurchaseorderhdr` | 15,148 | 0 | 3 | 2 | rows≈15,148, writes=0, reads=0, joins=10 |
| 37.6 | `public.smtbmmonthlyratehdr` | 1,928 | 5 | 5 | 4 | rows≈1,928, writes=0, reads=0, joins=9; has measures and a date column (possible fact table) |
| 37.5 | `public.smtbtemployeeleavemaster` | 57,146 | 1 | 5 | 0 | rows≈57,146, writes=0, reads=0, joins=8; has measures and a date column (possible fact table) |
| 37.1 | `public.smtbmemployee_old` | 349,421 | 5 | 25 | 19 | rows≈349,421, writes=0, reads=0, joins=10; name looks like log/backup/temp/framework table; has measures and a date column (possible fact table) |
| 36.8 | `public.smtbtquotation` | 826 | 3 | 4 | 5 | rows≈826, writes=0, reads=0, joins=9; has measures and a date column (possible fact table) |
| 36.7 | `public.smtbmemployee_audit` | 221,373 | 4 | 24 | 18 | rows≈221,373, writes=0, reads=0, joins=10; name looks like log/backup/temp/framework table; has measures and a date column (possible fact table) |
| 36.6 | `public.smtbtcustinvpaymenthdr` | 664,267 | 3 | 4 | 1 | rows≈664,267, writes=0, reads=0, joins=7; has measures and a date column (possible fact table) |
| 35.6 | `public.smtbmratecharthdr` | 6,398 | 2 | 4 | 3 | rows≈6,398, writes=0, reads=0, joins=8; has measures and a date column (possible fact table) |
| 32.8 | `public.smtbtcashdetails` | 7,887 | 9 | 6 | 4 | rows≈7,887, writes=0, reads=0, joins=7; has measures and a date column (possible fact table) |
| 32.6 | `public.smtbtmonthlysummary_staging` | 1,931 | 150 | 4 | 35 | rows≈1,931, writes=0, reads=0, joins=10; name looks like log/backup/temp/framework table; has measures and a date column (possible fact table) |
| 31.4 | `public.smtbtemployeefullfinalsalary` | 50,237 | 14 | 5 | 4 | rows≈50,237, writes=0, reads=0, joins=6; has measures and a date column (possible fact table) |
| 29.7 | `public.smtbtemployeefullfinalsalarydetail` | 216,810 | 1 | 2 | 3 | rows≈216,810, writes=0, reads=0, joins=5; has measures and a date column (possible fact table) |
| 29.6 | `public.smtbtsalarypaymentdtl` | 6,600,097 | 7 | 1 | 2 | rows≈6,600,097, writes=0, reads=0, joins=4; has measures and a date column (possible fact table) |
| 29.5 | `public.smtbmemployeeprofile` | 18,382 | 0 | 3 | 3 | rows≈18,382, writes=0, reads=0, joins=7 |
| 29.0 | `public.smtbtbulkinvoicehdr` | 10,224 | 0 | 3 | 2 | rows≈10,224, writes=0, reads=0, joins=7 |
| 28.7 | `public.smtbtloandetails` | 2,148,067 | 9 | 6 | 2 | rows≈2,148,067, writes=0, reads=0, joins=4; has measures and a date column (possible fact table) |
| 28.4 | `public.smtbtemployeeleavechild` | 1,498,156 | 5 | 2 | 0 | rows≈1,498,156, writes=0, reads=0, joins=4; has measures and a date column (possible fact table) |
| 28.3 | `public.smtbtcreditnote` | 44,930 | 1 | 3 | 1 | rows≈44,930, writes=0, reads=0, joins=5; has measures and a date column (possible fact table) |
| 28.3 | `public.smtbtholdpayhdr` | 136,319 | 0 | 5 | 3 | rows≈136,319, writes=0, reads=0, joins=6 |
| 28.1 | `public.smtbtpurchaseorderratedtl` | 3,648,492 | 9 | 0 | 0 | rows≈3,648,492, writes=0, reads=0, joins=5 |
| 28.0 | `public.smtbtbulkinvoicedtl` | 992,007 | 11 | 3 | 5 | rows≈992,007, writes=0, reads=0, joins=4; has measures and a date column (possible fact table) |
| 27.8 | `public.smtbtmiscsalaryhdr` | 82,960 | 0 | 3 | 3 | rows≈82,960, writes=0, reads=0, joins=6 |
| 27.5 | `public.smtbtarrearsdetailchild` | 560,279 | 15 | 2 | 2 | rows≈560,279, writes=0, reads=0, joins=4; has measures and a date column (possible fact table) |
| 27.5 | `public.smtbtemployeeleavechildhistory` | 556,403 | 5 | 2 | 1 | rows≈556,403, writes=0, reads=0, joins=4; has measures and a date column (possible fact table) |
| 27.5 | `public.smtbtbulkinvoiceratedtl` | 1,683,050 | 8 | 0 | 0 | rows≈1,683,050, writes=0, reads=0, joins=5 |
| 27.1 | `public.smtbtsociety` | 344,897 | 3 | 4 | 3 | rows≈344,897, writes=0, reads=0, joins=4; has measures and a date column (possible fact table) |
| 27.0 | `public.smtbtholdpaydtl` | 1,027,083 | 0 | 0 | 0 | rows≈1,027,083, writes=0, reads=0, joins=5 |
| 27.0 | `public.smtbgattendancestatus` | 315 | 1 | 2 | 4 | rows≈315, writes=0, reads=0, joins=6; has measures and a date column (possible fact table) |
| 26.8 | `public.smtbtinquiry` | 25,991 | 0 | 4 | 4 | rows≈25,991, writes=0, reads=0, joins=6 |
| 26.8 | `public.smtbgfinyear` | 24 | 0 | 4 | 0 | rows≈24, writes=0, reads=0, joins=8 |
| 26.7 | `public.smtbmdesignation` | 679 | 0 | 2 | 4 | rows≈679, writes=0, reads=0, joins=7 |
| 26.6 | `public.smtbmempsalaryheaddtl` | 205,106 | 1 | 3 | 4 | rows≈205,106, writes=0, reads=0, joins=4; has measures and a date column (possible fact table) |
| 26.6 | `public.smtbtarrearsdetail` | 198,820 | 2 | 2 | 2 | rows≈198,820, writes=0, reads=0, joins=4; has measures and a date column (possible fact table) |
| 26.2 | `public.smtbtbranchinvoicedtl` | 4,150 | 1 | 1 | 0 | rows≈4,150, writes=0, reads=0, joins=5; has measures and a date column (possible fact table) |
| 25.7 | `public.smtbtloanpayment` | 2,198,611 | 14 | 1 | 0 | rows≈2,198,611, writes=0, reads=0, joins=3; has measures and a date column (possible fact table) |
| 25.5 | `public.smtbmcustbrlochistory` | 5,862 | 0 | 2 | 2 | rows≈5,862, writes=0, reads=0, joins=6 |
| 25.2 | `public.smtbtemployeeleavesalarygeneral` | 41,821 | 29 | 4 | 4 | rows≈41,821, writes=0, reads=0, joins=4; has measures and a date column (possible fact table) |
| 24.8 | `public.smtbmdepartment` | 77 | 0 | 2 | 5 | rows≈77, writes=0, reads=0, joins=7 |
| 24.8 | `public.smtbtemployeebonussalarygeneral` | 23,793 | 53 | 3 | 2 | rows≈23,793, writes=0, reads=0, joins=4; has measures and a date column (possible fact table) |
| 24.8 | `public.dashboard_fact_billing_monthly` | 839,882 | 2 | 2 | 0 | rows≈839,882, writes=0, reads=0, joins=3; has measures and a date column (possible fact table) |
| 24.4 | `public.dashboard_fact_receipts_monthly` | 511,917 | 2 | 2 | 0 | rows≈511,917, writes=0, reads=0, joins=3; has measures and a date column (possible fact table) |
| 24.3 | `public.smtbtbghdr` | 425 | 2 | 6 | 6 | rows≈425, writes=0, reads=0, joins=5; has measures and a date column (possible fact table) |
| 24.3 | `public.smtbtarrearmonthlysummary` | 13 | 130 | 3 | 0 | rows≈13, writes=0, reads=0, joins=6; has measures and a date column (possible fact table) |
| 24.1 | `public.smtbmcustomershift` | 35,139 | 0 | 2 | 4 | rows≈35,139, writes=0, reads=0, joins=5 |
| 24.0 | `public.smtbtcustinvpaydtl` | 996,777 | 9 | 0 | 0 | rows≈996,777, writes=0, reads=0, joins=4 |
| 23.8 | `public.smtbmcustbrlocgstdet` | 23,884 | 0 | 2 | 4 | rows≈23,884, writes=0, reads=0, joins=5 |
| 23.7 | `public.smtbtarrearsdetailsummary` | 223,706 | 8 | 2 | 2 | rows≈223,706, writes=0, reads=0, joins=3; has measures and a date column (possible fact table) |
| 23.4 | `public.smtbtpurchaseorderratedtl_audit` | 1,597,949 | 9 | 1 | 1 | rows≈1,597,949, writes=0, reads=0, joins=5; name looks like log/backup/temp/framework table; has measures and a date column (possible fact table) |
| 23.2 | `public.smtbtarrearinvoicedtl` | 3 | 1 | 3 | 0 | rows≈3, writes=0, reads=0, joins=6; has measures and a date column (possible fact table) |
| 23.1 | `public.smtbtemployeeleavemasterhistory` | 3,590 | 1 | 6 | 3 | rows≈3,590, writes=0, reads=0, joins=4; has measures and a date column (possible fact table) |
| 23.1 | `public.smtbtbulkinvoiceotherratedtl` | 374,667 | 3 | 0 | 1 | rows≈374,667, writes=0, reads=0, joins=4 |
| 22.9 | `public.smtbtadvance` | 2,974 | 2 | 2 | 2 | rows≈2,974, writes=0, reads=0, joins=4; has measures and a date column (possible fact table) |
| 22.9 | `public.smtbmshift` | 8 | 0 | 2 | 0 | rows≈8, writes=0, reads=0, joins=7 |
| 22.8 | `public.smtbtemployeebonuschild` | 2,507,328 | 2 | 2 | 1 | rows≈2,507,328, writes=0, reads=0, joins=2; has measures and a date column (possible fact table) |
| 22.8 | `public.smtbtemployeeleavesummaryhistory` | 83,408 | 6 | 2 | 1 | rows≈83,408, writes=0, reads=0, joins=3; has measures and a date column (possible fact table) |
| 22.8 | `public.smtbtpaymentreturndetails` | 8,315 | 0 | 2 | 1 | rows≈8,315, writes=0, reads=0, joins=5 |
| 22.7 | `public.smtbtemployeebonusmaster` | 70,335 | 3 | 5 | 0 | rows≈70,335, writes=0, reads=0, joins=3; has measures and a date column (possible fact table) |
| 22.6 | `public.smtbtbranchinvoiceratedtl` | 6,235 | 8 | 0 | 0 | rows≈6,235, writes=0, reads=0, joins=5 |
| 22.5 | `public.smtbtleaveapplication` | 56,259 | 4 | 8 | 0 | rows≈56,259, writes=0, reads=0, joins=3; has measures and a date column (possible fact table) |
| 22.5 | `public.smtbmratezone` | 169 | 0 | 2 | 5 | rows≈169, writes=0, reads=0, joins=6 |
| 22.3 | `public.smtbtworkorderratedtl` | 142,692 | 3 | 0 | 0 | rows≈142,692, writes=0, reads=0, joins=4 |
| 22.2 | `public.smtbminsurance` | 1,323 | 1 | 4 | 4 | rows≈1,323, writes=0, reads=0, joins=4; has measures and a date column (possible fact table) |
| 22.0 | `public.smtbtemployeebonusmaster1` | 32,272 | 3 | 5 | 1 | rows≈32,272, writes=0, reads=0, joins=3; has measures and a date column (possible fact table) |
| 22.0 | `public.smtbtemployeebonuschild1` | 1,048,738 | 2 | 2 | 1 | rows≈1,048,738, writes=0, reads=0, joins=2; has measures and a date column (possible fact table) |
| 21.8 | `public.smtbtmiscsalarydtl` | 83,565 | 1 | 0 | 0 | rows≈83,565, writes=0, reads=0, joins=4 |
| 21.0 | `public.smtbtquotationratedtl` | 31,155 | 2 | 0 | 0 | rows≈31,155, writes=0, reads=0, joins=4 |
| 20.8 | `public.smtbtarrearssalarydtl` | 8,047 | 8 | 1 | 0 | rows≈8,047, writes=0, reads=0, joins=3; has measures and a date column (possible fact table) |
| 20.8 | `public.smtbtcreditdebitreceiptno` | 23,768 | 0 | 0 | 2 | rows≈23,768, writes=0, reads=0, joins=4 |
| 20.8 | `public.smtbtcustinquiry` | 8,228 | 1 | 3 | 1 | rows≈8,228, writes=0, reads=0, joins=3; has measures and a date column (possible fact table) |
| 20.7 | `public.smtbtemployeeleavesummary` | 219,842 | 7 | 2 | 1 | rows≈219,842, writes=0, reads=0, joins=2; has measures and a date column (possible fact table) |
| 20.7 | `public.smtbtbulkinvoicegstdetails` | 680,739 | 10 | 0 | 0 | rows≈680,739, writes=0, reads=0, joins=3 |
| 20.4 | `public.smtbtsdhdr` | 4 | 1 | 6 | 0 | rows≈4, writes=0, reads=0, joins=5; has measures and a date column (possible fact table) |
| 20.4 | `public.smtbmptaxslabhdr` | 516 | 0 | 3 | 5 | rows≈516, writes=0, reads=0, joins=5 |
| 20.2 | `public.smtbtemployeebonusmasterhistory` | 4,121 | 3 | 6 | 3 | rows≈4,121, writes=0, reads=0, joins=3; has measures and a date column (possible fact table) |
| 19.9 | `public.smtbmodule` | 293 | 0 | 0 | 1 | rows≈293, writes=0, reads=0, joins=5 |
| 19.7 | `public.smtbtarrearinvoiceratedtl` | 6 | 7 | 0 | 0 | rows≈6, writes=0, reads=0, joins=6 |
| 19.6 | `public.smtbtsalarypaymenthdr` | 200,092 | 0 | 3 | 2 | rows≈200,092, writes=0, reads=0, joins=3 |
| 19.4 | `public.smtbtvendortransactiondtl` | 50,068 | 2 | 2 | 5 | rows≈50,068, writes=0, reads=0, joins=2; has measures and a date column (possible fact table) |
| 19.3 | `public.payroll_run` | 43 | 4 | 2 | 7 | rows≈43, writes=0, reads=0, joins=4; has measures and a date column (possible fact table) |
| 18.8 | `public.smtbmempsalheadhistorydtl` | 822 | 1 | 1 | 0 | rows≈822, writes=0, reads=0, joins=3; has measures and a date column (possible fact table) |
| 18.4 | `public.smtbmbankcategory` | 52 | 0 | 2 | 5 | rows≈52, writes=0, reads=0, joins=5 |
| 18.4 | `public.smtbtcommonprocesshdr` | 48,623 | 0 | 3 | 1 | rows≈48,623, writes=0, reads=0, joins=3 |
| 18.2 | `public.smtbtemployeebonussummary` | 381,926 | 7 | 2 | 0 | rows≈381,926, writes=0, reads=0, joins=1; has measures and a date column (possible fact table) |
| 18.1 | `public.smtbtemdhdr` | 369 | 1 | 6 | 8 | rows≈369, writes=0, reads=0, joins=3; has measures and a date column (possible fact table) |
| 18.0 | `public.smtbmarrearssalary` | 317 | 1 | 4 | 0 | rows≈317, writes=0, reads=0, joins=3; has measures and a date column (possible fact table) |
| 18.0 | `public.smtbgratebasishdr` | 301 | 1 | 2 | 5 | rows≈301, writes=0, reads=0, joins=3; has measures and a date column (possible fact table) |
| 17.9 | `public.smtbtemployeebonuschildhistory` | 8,829 | 2 | 2 | 2 | rows≈8,829, writes=0, reads=0, joins=2; has measures and a date column (possible fact table) |
| 17.9 | `public.smtbgactiveuser` | 906 | 0 | 1 | 2 | rows≈906, writes=0, reads=0, joins=4 |
| 17.7 | `public.smtbmratechartdtl` | 22,996 | 3 | 0 | 0 | rows≈22,996, writes=0, reads=0, joins=3 |
| 17.4 | `public.smtbtagreementhdr` | 4 | 1 | 6 | 0 | rows≈4, writes=0, reads=0, joins=4; has measures and a date column (possible fact table) |
| 17.2 | `public.smtbtvendortransactionhdr` | 13,266 | 0 | 3 | 4 | rows≈13,266, writes=0, reads=0, joins=3 |
| 17.1 | `public.smtbmemployee_bankdetails` | 349,421 | 0 | 2 | 2 | rows≈349,421, writes=0, reads=0, joins=2 |
| 16.8 | `public.smtbmresourcegroup` | 256 | 0 | 2 | 4 | rows≈256, writes=0, reads=0, joins=4 |
| 16.7 | `public.smtbmbranchholidayhdr` | 233 | 0 | 2 | 4 | rows≈233, writes=0, reads=0, joins=4 |
| 16.3 | `public.smtbguseraccesspermission` | 140,346 | 0 | 2 | 2 | rows≈140,346, writes=0, reads=0, joins=2 |
| 16.1 | `public.smtbmvendorpayheads` | 3,403 | 0 | 2 | 4 | rows≈3,403, writes=0, reads=0, joins=3 |
| 16.0 | `public.smtbtemployeebonussummaryhistory` | 1,045 | 6 | 2 | 1 | rows≈1,045, writes=0, reads=0, joins=2; has measures and a date column (possible fact table) |
| 16.0 | `public.smtbmmonthlyratedtl` | 95,923 | 2 | 0 | 0 | rows≈95,923, writes=0, reads=0, joins=2 |
| 16.0 | `public.smtbmresourcenew` | 3,068 | 0 | 2 | 2 | rows≈3,068, writes=0, reads=0, joins=3 |
| 15.9 | `public.dashboard_fact_aging_customer` | 887 | 5 | 2 | 0 | rows≈887, writes=0, reads=0, joins=2; has measures and a date column (possible fact table) |
| 15.6 | `public.smtbttrainingdtl` | 61,405 | 0 | 0 | 0 | rows≈61,405, writes=0, reads=0, joins=2 |
| 15.3 | `public.smtbtquotationdtl` | 1,351 | 10 | 0 | 0 | rows≈1,351, writes=0, reads=0, joins=3 |
| 15.2 | `public.smtbtsocietywef` | 11,903 | 1 | 1 | 1 | rows≈11,903, writes=0, reads=0, joins=1; has measures and a date column (possible fact table) |
| 15.2 | `public.smtbmcustlocgroupdtl` | 38,551 | 0 | 0 | 0 | rows≈38,551, writes=0, reads=0, joins=2 |
| 15.1 | `public.smtbtconsolidateinvsequence` | 37,542 | 0 | 0 | 0 | rows≈37,542, writes=0, reads=0, joins=2 |
| 15.1 | `public.smtbtconsolidateinvno` | 37,529 | 0 | 0 | 0 | rows≈37,529, writes=0, reads=0, joins=2 |
| 15.1 | `public.smtbmemployee_personal` | 349,421 | 3 | 2 | 4 | rows≈349,421, writes=0, reads=0, joins=0; has measures and a date column (possible fact table) |
| 15.1 | `public.smtbmemployee_other` | 349,421 | 1 | 13 | 2 | rows≈349,421, writes=0, reads=0, joins=0; has measures and a date column (possible fact table) |
| 15.0 | `public.smtbtleavedetail` | 32,678 | 8 | 0 | 0 | rows≈32,678, writes=0, reads=0, joins=2 |
| 14.9 | `public.smtbtbdr` | 9,010 | 10 | 2 | 4 | rows≈9,010, writes=0, reads=0, joins=1; has measures and a date column (possible fact table) |
| 14.8 | `public.smtbtusedrecovery` | 7,665 | 1 | 2 | 0 | rows≈7,665, writes=0, reads=0, joins=1; has measures and a date column (possible fact table) |
| 14.6 | `public.smtbtbulkinvoicedtldelete` | 19,521 | 0 | 1 | 1 | rows≈19,521, writes=0, reads=0, joins=2 |
| 14.4 | `public.smtbtuserpermbranch` | 15,847 | 0 | 0 | 0 | rows≈15,847, writes=0, reads=0, joins=2 |
| 14.1 | `public.smtbtbulkinvoiceotherdatadtl` | 10 | 0 | 1 | 0 | rows≈10, writes=0, reads=0, joins=4 |
| 13.9 | `public.smtbmemployeedtl` | 91 | 1 | 3 | 5 | rows≈91, writes=0, reads=0, joins=2; has measures and a date column (possible fact table) |
| 13.8 | `public.smtbmrecoveryusedagcn` | 79 | 3 | 1 | 0 | rows≈79, writes=0, reads=0, joins=2; has measures and a date column (possible fact table) |
| 13.8 | `public.smtbmarrearssummary` | 7,927 | 1 | 0 | 0 | rows≈7,927, writes=0, reads=0, joins=2 |
| 13.6 | `public.tally` | 61,853 | 1 | 1 | 1 | rows≈61,853, writes=0, reads=0, joins=0; has measures and a date column (possible fact table) |
| 13.5 | `public.smtbgjobrolepermission` | 5,809 | 0 | 2 | 4 | rows≈5,809, writes=0, reads=0, joins=2 |
| 13.4 | `public.gst` | 51,138 | 2 | 1 | 2 | rows≈51,138, writes=0, reads=0, joins=0; has measures and a date column (possible fact table) |
| 13.4 | `public.tallysales` | 50,567 | 3 | 1 | 4 | rows≈50,567, writes=0, reads=0, joins=0; has measures and a date column (possible fact table) |
| 13.4 | `public.smtbmgradedtl` | 5,305 | 2 | 0 | 0 | rows≈5,305, writes=0, reads=0, joins=2 |
| 13.4 | `public.smtbgreportformat` | 166 | 0 | 2 | 7 | rows≈166, writes=0, reads=0, joins=3 |
| 13.3 | `public.smtbgpayslipheaderhdr` | 42 | 1 | 2 | 0 | rows≈42, writes=0, reads=0, joins=2; has measures and a date column (possible fact table) |
| 13.2 | `public.smtbmtype` | 3 | 0 | 1 | 0 | rows≈3, writes=0, reads=0, joins=4 |
| 13.1 | `public.smtbmclientexcemption` | 3,362 | 0 | 2 | 2 | rows≈3,362, writes=0, reads=0, joins=2 |
| 13.0 | `public.smtbmemployeepvdetails` | 101,704 | 0 | 5 | 1 | rows≈101,704, writes=0, reads=0, joins=1 |
| 12.7 | `public.smtbmservices` | 72 | 0 | 2 | 4 | rows≈72, writes=0, reads=0, joins=3 |
| 12.6 | `public.smtbmitemdefinition` | 1 | 0 | 2 | 0 | rows≈1, writes=0, reads=0, joins=4 |
| 12.5 | `public.smtbtemployeearrearsalary` | 17 | 17 | 2 | 0 | rows≈17, writes=0, reads=0, joins=2; has measures and a date column (possible fact table) |
| 12.4 | `public.smtbgratebasisdtl` | 1,580 | 0 | 0 | 0 | rows≈1,580, writes=0, reads=0, joins=2 |
| 12.4 | `public.smtbgpayslipdetailhdr` | 15 | 1 | 2 | 0 | rows≈15, writes=0, reads=0, joins=2; has measures and a date column (possible fact table) |
| 12.3 | `public.smtbmbranchholidaydtl` | 1,393 | 0 | 1 | 0 | rows≈1,393, writes=0, reads=0, joins=2 |
| 12.2 | `public.smtbmcustomerhistory` | 38 | 0 | 2 | 0 | rows≈38, writes=0, reads=0, joins=3 |
| 12.2 | `public.esicsubcode` | 41,456 | 0 | 0 | 1 | rows≈41,456, writes=0, reads=0, joins=1 |
| 11.7 | `public.smtbguserdefinedrptperm` | 739 | 1 | 0 | 0 | rows≈739, writes=0, reads=0, joins=2 |
| 11.7 | `public.smtbminvoiceconsogrphdr` | 724 | 0 | 2 | 0 | rows≈724, writes=0, reads=0, joins=2 |
| 11.7 | `public.smtbmemployeegroupdtl` | 743 | 0 | 0 | 0 | rows≈743, writes=0, reads=0, joins=2 |
| 11.4 | `public.smtbmleaveslab_master` | 14 | 0 | 2 | 0 | rows≈14, writes=0, reads=0, joins=3 |
| 11.3 | `public.smtbthradedemplistdtl` | 463 | 0 | 0 | 0 | rows≈463, writes=0, reads=0, joins=2 |
| 11.2 | `public.regional_settings` | 129 | 8 | 2 | 3 | rows≈129, writes=0, reads=0, joins=1; has measures and a date column (possible fact table) |
| 11.1 | `public.smtbmemployee_pf_esic` | 349,421 | 0 | 4 | 4 | rows≈349,421, writes=0, reads=0, joins=0 |
| 11.1 | `public.smtbmemployee_address` | 349,421 | 0 | 0 | 0 | rows≈349,421, writes=0, reads=0, joins=0 |
| 11.1 | `public.smtbmemployee_policverification` | 349,421 | 0 | 4 | 4 | rows≈349,421, writes=0, reads=0, joins=0 |
| 11.0 | `public.smtbtcustsalarypaymentdtl` | 2 | 3 | 3 | 0 | rows≈2, writes=0, reads=0, joins=2; has measures and a date column (possible fact table) |
| 10.7 | `public.guard` | 2,266 | 3 | 2 | 1 | rows≈2,266, writes=0, reads=0, joins=0; has measures and a date column (possible fact table) |
| 10.7 | `public.smtbmprincipalrtamount` | 70 | 1 | 2 | 0 | rows≈70, writes=0, reads=0, joins=1; has measures and a date column (possible fact table) |
| 10.7 | `public.smtbminvoiceconsogrpdtl` | 7,485 | 0 | 0 | 0 | rows≈7,485, writes=0, reads=0, joins=1 |
| 10.7 | `public.smtbmneftmaster` | 6 | 0 | 3 | 0 | rows≈6, writes=0, reads=0, joins=3 |
| 10.7 | `public.servicetax1718` | 2,276 | 11 | 1 | 10 | rows≈2,276, writes=0, reads=0, joins=0; has measures and a date column (possible fact table) |
| 10.6 | `public.dashboard_fact_outstanding_branch` | 64 | 2 | 2 | 0 | rows≈64, writes=0, reads=0, joins=1; has measures and a date column (possible fact table) |
| 10.6 | `public.asperbayer` | 1,953 | 5 | 2 | 6 | rows≈1,953, writes=0, reads=0, joins=0; has measures and a date column (possible fact table) |
| 10.6 | `public.smtbmcustomershifttemp` | 193 | 0 | 2 | 7 | rows≈193, writes=0, reads=0, joins=2 |
| 10.6 | `public.custlot` | 6,392 | 0 | 0 | 0 | rows≈6,392, writes=0, reads=0, joins=1 |
| 10.6 | `public.smtbmgst` | 62 | 5 | 3 | 0 | rows≈62, writes=0, reads=0, joins=1; has measures and a date column (possible fact table) |
| 10.5 | `public.smtbmrandtamount` | 58 | 1 | 2 | 0 | rows≈58, writes=0, reads=0, joins=1; has measures and a date column (possible fact table) |
| 10.4 | `public.smtbmcustlocgroup` | 4 | 0 | 2 | 0 | rows≈4, writes=0, reads=0, joins=3 |
| 10.4 | `public.smtbtsalarypaymentaudit` | 165,350 | 0 | 1 | 2 | rows≈165,350, writes=0, reads=0, joins=0 |
| 10.1 | `public.smtbmindustry` | 113 | 0 | 2 | 5 | rows≈113, writes=0, reads=0, joins=2 |
| 10.0 | `public.newcontract` | 3,174 | 2 | 0 | 2 | rows≈3,174, writes=0, reads=0, joins=1 |
| 10.0 | `public.smtbmneftdetails` | 30 | 4 | 2 | 0 | rows≈30, writes=0, reads=0, joins=1; has measures and a date column (possible fact table) |
| 10.0 | `public.empaccno` | 96 | 0 | 0 | 1 | rows≈96, writes=0, reads=0, joins=2 |
| 9.7 | `public.closedcontract` | 2,231 | 2 | 0 | 3 | rows≈2,231, writes=0, reads=0, joins=1 |
| 9.6 | `public.smtbmleaveslab_details` | 20 | 4 | 2 | 0 | rows≈20, writes=0, reads=0, joins=1; has measures and a date column (possible fact table) |
| 9.6 | `public.smtbgunlocktransactions` | 1 | 0 | 1 | 0 | rows≈1, writes=0, reads=0, joins=3 |
| 9.6 | `public.smtbtbranchinvoice` | 63 | 0 | 3 | 5 | rows≈63, writes=0, reads=0, joins=2 |
| 9.6 | `public.smtbmcategory` | 1 | 0 | 2 | 0 | rows≈1, writes=0, reads=0, joins=3 |
| 9.5 | `public.smtbminsuranceskipdtl` | 1,704 | 0 | 0 | 0 | rows≈1,704, writes=0, reads=0, joins=1 |
| 9.4 | `public.finaldata` | 48,942 | 8 | 0 | 2 | rows≈48,942, writes=0, reads=0, joins=0 |
| 9.4 | `public.temptableuanno` | 1,525 | 0 | 0 | 0 | rows≈1,525, writes=0, reads=0, joins=1 |
| 9.4 | `public.smtbmptaxslabdtl` | 1,498 | 4 | 0 | 0 | rows≈1,498, writes=0, reads=0, joins=1 |
| 9.4 | `public.smtbtarrearssalarych_dtl` | 48,348 | 3 | 0 | 0 | rows≈48,348, writes=0, reads=0, joins=0 |
| 9.3 | `public.smtbmresourcegroupnew` | 1,374 | 0 | 2 | 4 | rows≈1,374, writes=0, reads=0, joins=1 |
| 9.3 | `public.smtbmjobrole` | 42 | 0 | 2 | 0 | rows≈42, writes=0, reads=0, joins=2 |
| 9.3 | `public.pd_table` | 42,351 | 1 | 0 | 1 | rows≈42,351, writes=0, reads=0, joins=0 |
| 8.9 | `public.auditlogs` | 921 | 0 | 1 | 8 | rows≈921, writes=0, reads=0, joins=1 |
| 8.9 | `public.payroll_run_step` | 843 | 0 | 2 | 5 | rows≈843, writes=0, reads=0, joins=1 |
| 8.8 | `public.smtbthradedemplisthdr` | 25 | 0 | 2 | 0 | rows≈25, writes=0, reads=0, joins=2 |
| 8.8 | `public.bonuscad` | 25,428 | 1 | 0 | 1 | rows≈25,428, writes=0, reads=0, joins=0 |
| 8.7 | `public.smtbmcustlocgrouphdr` | 22 | 0 | 2 | 0 | rows≈22, writes=0, reads=0, joins=2 |
| 8.6 | `public.smtbgformuladtl` | 18 | 0 | 0 | 0 | rows≈18, writes=0, reads=0, joins=2 |
| 8.5 | `public.smtbgpayslipdetaildtl` | 545 | 0 | 0 | 2 | rows≈545, writes=0, reads=0, joins=1 |
| 8.4 | `public.bisuidnos` | 15,344 | 3 | 0 | 1 | rows≈15,344, writes=0, reads=0, joins=0 |
| 8.4 | `public.smtbgpayslipheaderdtl` | 524 | 0 | 0 | 2 | rows≈524, writes=0, reads=0, joins=1 |
| 7.9 | `public.rptprlguardsalarydetail` | 280 | 0 | 0 | 5 | rows≈280, writes=0, reads=0, joins=1 |
| 7.8 | `public.smtbtcustpaymenthdr` | 7 | 0 | 3 | 0 | rows≈7, writes=0, reads=0, joins=2 |
| 7.8 | `public.staff` | 78 | 3 | 2 | 7 | rows≈78, writes=0, reads=0, joins=0; has measures and a date column (possible fact table) |
| 7.8 | `public.smtbtagreementdtl` | 7 | 0 | 0 | 0 | rows≈7, writes=0, reads=0, joins=2 |
| 7.7 | `public.smtbgempwisegrouphdr` | 6 | 0 | 0 | 0 | rows≈6, writes=0, reads=0, joins=2 |
| 7.7 | `public.bonpo` | 6,858 | 1 | 0 | 1 | rows≈6,858, writes=0, reads=0, joins=0 |
| 7.6 | `public.smtbmemployeegrouphdr` | 5 | 0 | 3 | 0 | rows≈5, writes=0, reads=0, joins=2 |
| 7.6 | `public.temp_day7` | 66,518 | 0 | 0 | 1 | rows≈66,518, writes=0, reads=0, joins=2; name looks like log/backup/temp/framework table |
| 7.3 | `public.smtbmbranchcode` | 146 | 0 | 0 | 0 | rows≈146, writes=0, reads=0, joins=1 |
| 7.2 | `public.smtbtarrearinvoicehdr` | 3 | 0 | 3 | 0 | rows≈3, writes=0, reads=0, joins=2 |
| 7.2 | `public.smtbtpurchaseorderotherdtl` | 3 | 0 | 1 | 0 | rows≈3, writes=0, reads=0, joins=2 |
| 7.1 | `public.getemp` | 105 | 1 | 0 | 0 | rows≈105, writes=0, reads=0, joins=1 |
| 7.1 | `public.erpuanno` | 3,577 | 0 | 0 | 0 | rows≈3,577, writes=0, reads=0, joins=0 |
| 7.0 | `public.smtbmcustcatagory` | 2 | 0 | 2 | 0 | rows≈2, writes=0, reads=0, joins=2 |
| 7.0 | `public.wild` | 101 | 1 | 0 | 5 | rows≈101, writes=0, reads=0, joins=1 |
| 7.0 | `public.smtbmfamily` | 2 | 0 | 2 | 0 | rows≈2, writes=0, reads=0, joins=2 |
| 6.7 | `public.upload` | 2,178 | 0 | 2 | 1 | rows≈2,178, writes=0, reads=0, joins=0 |
| 6.6 | `public.pd_pending` | 2,054 | 1 | 0 | 1 | rows≈2,054, writes=0, reads=0, joins=0 |
| 6.3 | `public.expenses` | 1,368 | 2 | 0 | 2 | rows≈1,368, writes=0, reads=0, joins=0 |
| 6.3 | `public.updatedojldw` | 1,491 | 0 | 2 | 1 | rows≈1,491, writes=0, reads=0, joins=0 |
| 6.2 | `public.smtbgwagereportformat` | 40 | 0 | 2 | 0 | rows≈40, writes=0, reads=0, joins=1 |
| 6.2 | `public.smtbmtrainingtype` | 37 | 0 | 2 | 0 | rows≈37, writes=0, reads=0, joins=1 |
| 5.9 | `public.erpsales` | 841 | 10 | 0 | 11 | rows≈841, writes=0, reads=0, joins=0 |
| 5.8 | `public.smtbmpohours` | 7 | 1 | 2 | 0 | rows≈7, writes=0, reads=0, joins=0; has measures and a date column (possible fact table) |
| 5.8 | `public.tempticket` | 840 | 0 | 0 | 0 | rows≈840, writes=0, reads=0, joins=0 |
| 5.8 | `public.gorakhpur` | 756 | 1 | 0 | 0 | rows≈756, writes=0, reads=0, joins=0 |
| 5.7 | `public.tempuanno` | 686 | 0 | 0 | 0 | rows≈686, writes=0, reads=0, joins=0 |
| 5.7 | `public.vehiclemovement` | 697 | 0 | 0 | 14 | rows≈697, writes=0, reads=0, joins=0 |
| 5.7 | `public.smtbmservicetax` | 6 | 6 | 3 | 0 | rows≈6, writes=0, reads=0, joins=0; has measures and a date column (possible fact table) |
| 5.7 | `public.smtbgreportformula` | 6 | 1 | 2 | 0 | rows≈6, writes=0, reads=0, joins=0; has measures and a date column (possible fact table) |
| 5.6 | `public.vendordetails` | 665 | 0 | 0 | 3 | rows≈665, writes=0, reads=0, joins=0 |
| 5.3 | `public.smtbmholiday` | 13 | 0 | 2 | 0 | rows≈13, writes=0, reads=0, joins=1 |
| 5.2 | `public.hsncode` | 398 | 2 | 0 | 0 | rows≈398, writes=0, reads=0, joins=0 |
| 5.2 | `public.retainer` | 386 | 0 | 1 | 2 | rows≈386, writes=0, reads=0, joins=0 |
| 5.2 | `public.tempticketno` | 398 | 0 | 0 | 0 | rows≈398, writes=0, reads=0, joins=0 |
| 5.0 | `public.vapirecovery` | 313 | 0 | 0 | 0 | rows≈313, writes=0, reads=0, joins=0 |
| 5.0 | `public.smtbmsalaryheaddetail` | 2 | 1 | 1 | 0 | rows≈2, writes=0, reads=0, joins=0; has measures and a date column (possible fact table) |
| 4.8 | `public.details` | 244 | 2 | 0 | 2 | rows≈244, writes=0, reads=0, joins=0 |
| 4.7 | `public.sagaraudit` | 216 | 1 | 0 | 1 | rows≈216, writes=0, reads=0, joins=0 |
| 4.6 | `public.smtbgempwisegroupdtl` | 5 | 0 | 0 | 0 | rows≈5, writes=0, reads=0, joins=1 |
| 4.3 | `public.guardesicno` | 139 | 0 | 1 | 0 | rows≈139, writes=0, reads=0, joins=0 |
| 4.3 | `public.smtbmoduleold` | 133 | 0 | 0 | 2 | rows≈133, writes=0, reads=0, joins=0 |
| 4.3 | `public.flgp` | 137 | 0 | 0 | 0 | rows≈137, writes=0, reads=0, joins=0 |
| 4.2 | `public.smtbgmonth` | 132 | 0 | 0 | 0 | rows≈132, writes=0, reads=0, joins=0 |
| 4.0 | `public.smtbmmake` | 2 | 0 | 2 | 0 | rows≈2, writes=0, reads=0, joins=1 |
| 4.0 | `public.card` | 100 | 2 | 0 | 5 | rows≈100, writes=0, reads=0, joins=0 |
| 3.9 | `public.punels` | 91 | 4 | 0 | 2 | rows≈91, writes=0, reads=0, joins=0 |
| 3.9 | `public.bisdoubleneft` | 93 | 3 | 0 | 3 | rows≈93, writes=0, reads=0, joins=0 |
| 3.7 | `public.societynos` | 68 | 0 | 0 | 2 | rows≈68, writes=0, reads=0, joins=0 |
| 3.6 | `public.smtbm_taglinemast` | 1 | 0 | 0 | 0 | rows≈1, writes=0, reads=0, joins=1 |
| 3.6 | `public.smtbmachead` | 1 | 0 | 2 | 0 | rows≈1, writes=0, reads=0, joins=1 |
| 3.5 | `public.thanet` | 58 | 0 | 0 | 1 | rows≈58, writes=0, reads=0, joins=0 |
| 2.5 | `public.dashboard_widget_definition` | 16 | 0 | 2 | 4 | rows≈16, writes=0, reads=0, joins=0 |
| 2.2 | `public.smtbmpoinvtype` | 11 | 0 | 0 | 0 | rows≈11, writes=0, reads=0, joins=0 |
| 1.9 | `public.smtbgreceiptmode` | 8 | 0 | 0 | 0 | rows≈8, writes=0, reads=0, joins=0 |
| 1.4 | `public.payroll_run_log` | 1,541 | 0 | 1 | 2 | rows≈1,541, writes=0, reads=0, joins=1; name looks like log/backup/temp/framework table |
| 1.0 | `public.smtbmleavetype` | 2 | 0 | 2 | 0 | rows≈2, writes=0, reads=0, joins=0 |
| 0.6 | `public.smtbgmessagedetails` | 1 | 0 | 1 | 0 | rows≈1, writes=0, reads=0, joins=0 |
| 0.6 | `public.smtbgageing` | 1 | 0 | 1 | 0 | rows≈1, writes=0, reads=0, joins=0 |
| -0.1 | `public.smtbmodule_backup` | 292 | 0 | 0 | 0 | rows≈292, writes=0, reads=0, joins=1; name looks like log/backup/temp/framework table |
| -3.5 | `public.temp` | 171 | 0 | 2 | 2 | rows≈171, writes=0, reads=0, joins=0; name looks like log/backup/temp/framework table |
| -66.0 | `public.smtbtinvoicehdr` | 0 | 2 | 4 | 0 | rows≈0, writes=0, reads=0, joins=10; empty; has measures and a date column (possible fact table) |
| -73.0 | `public.tempsmtbtdailyattendance` | 0 | 0 | 6 | 0 | rows≈0, writes=0, reads=0, joins=9; empty |
| -79.0 | `public.smtbmemployeeprofiletemp` | 0 | 0 | 3 | 0 | rows≈0, writes=0, reads=0, joins=7; empty |
| -82.0 | `public.smtbtdeploymentdtl` | 0 | 0 | 2 | 0 | rows≈0, writes=0, reads=0, joins=6; empty |
| -85.0 | `public.smtbtinvoicedtl` | 0 | 4 | 0 | 0 | rows≈0, writes=0, reads=0, joins=5; empty |
| -85.0 | `public.smtbmvendor` | 0 | 0 | 2 | 0 | rows≈0, writes=0, reads=0, joins=5; empty |
| -86.0 | `public.smtbtpurchaseorderdtl_audit` | 0 | 16 | 17 | 0 | rows≈0, writes=0, reads=0, joins=6; empty; name looks like log/backup/temp/framework table; has measures and a date column (possible fact table) |
| -87.0 | `public.smtbtadvancedetail` | 0 | 1 | 2 | 0 | rows≈0, writes=0, reads=0, joins=3; empty; has measures and a date column (possible fact table) |
| -87.0 | `public.smtbtemployeegratuitysalary` | 0 | 28 | 3 | 0 | rows≈0, writes=0, reads=0, joins=3; empty; has measures and a date column (possible fact table) |
| -88.0 | `public.smtbtdeploymenthdr` | 0 | 0 | 4 | 0 | rows≈0, writes=0, reads=0, joins=4; empty |
| -88.0 | `public.smtbtbankguaranty` | 0 | 0 | 6 | 0 | rows≈0, writes=0, reads=0, joins=4; empty |
| -89.0 | `public.smtbmcustomer_audit` | 0 | 1 | 3 | 0 | rows≈0, writes=0, reads=0, joins=5; empty; name looks like log/backup/temp/framework table; has measures and a date column (possible fact table) |
| -90.0 | `public.smtbgformulahdr` | 0 | 1 | 2 | 0 | rows≈0, writes=0, reads=0, joins=2; empty; has measures and a date column (possible fact table) |
| -91.0 | `public.smtbminvoiceconsogrptmp` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=3; empty |
| -91.0 | `public.smtbmempsalaryheaddtltemp` | 0 | 1 | 0 | 0 | rows≈0, writes=0, reads=0, joins=3; empty |
| -91.0 | `public.brs_momentorder` | 0 | 0 | 1 | 0 | rows≈0, writes=0, reads=0, joins=3; empty |
| -93.0 | `public.smtbalertoutbox` | 0 | 1 | 4 | 1 | rows≈0, writes=0, reads=0, joins=1; empty; has measures and a date column (possible fact table) |
| -94.0 | `public.smtbtratebreakup` | 0 | 2 | 0 | 0 | rows≈0, writes=0, reads=0, joins=2; empty |
| -94.0 | `public.background_job_definition` | 0 | 0 | 2 | 1 | rows≈0, writes=0, reads=0, joins=2; empty |
| -94.0 | `public.smtbtconsomst` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=2; empty |
| -94.0 | `public.smtbmcityduplicate` | 0 | 0 | 2 | 0 | rows≈0, writes=0, reads=0, joins=2; empty |
| -94.0 | `public.smtbtposting` | 0 | 0 | 5 | 0 | rows≈0, writes=0, reads=0, joins=2; empty |
| -94.0 | `public.accountno` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=2; empty |
| -94.0 | `public.smtbglocktransation` | 0 | 0 | 1 | 0 | rows≈0, writes=0, reads=0, joins=2; empty |
| -94.0 | `public.recovery` | 0 | 1 | 0 | 0 | rows≈0, writes=0, reads=0, joins=2; empty |
| -96.0 | `public.otslabs` | 0 | 3 | 1 | 0 | rows≈0, writes=0, reads=0, joins=0; empty; has measures and a date column (possible fact table) |
| -96.0 | `public.smtbgpayrollsetup` | 0 | 9 | 4 | 0 | rows≈0, writes=0, reads=0, joins=0; empty; has measures and a date column (possible fact table) |
| -97.0 | `public.empdob` | 0 | 0 | 1 | 0 | rows≈0, writes=0, reads=0, joins=1; empty |
| -97.0 | `public.smtbmsalaryhdeffdate` | 0 | 0 | 1 | 0 | rows≈0, writes=0, reads=0, joins=1; empty |
| -97.0 | `public.menupad` | 0 | 1 | 0 | 0 | rows≈0, writes=0, reads=0, joins=1; empty |
| -97.0 | `public.dashboard_user_layout` | 0 | 0 | 2 | 0 | rows≈0, writes=0, reads=0, joins=1; empty |
| -97.0 | `public.mst_trainingcentre` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=1; empty |
| -97.0 | `public.smtbusermodule` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=1; empty |
| -97.0 | `public.esicnopf` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=1; empty |
| -97.0 | `public.temprelf` | 0 | 2 | 0 | 0 | rows≈0, writes=0, reads=0, joins=1; empty |
| -97.0 | `public.payrollstep_masterlist` | 0 | 0 | 2 | 2 | rows≈0, writes=0, reads=0, joins=1; empty |
| -97.0 | `public.smtbgleavetype` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=1; empty |
| -100.0 | `public.smtbminvoiceirintingtype` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbmgender` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.v_strheads` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbmeligibilitytype` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbmbonusrpttype` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbminquirystatus` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbmpaymentmode` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.raigarhdoj` | 0 | 0 | 1 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbalerttemplate` | 0 | 0 | 2 | 1 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbgsalaryheadratebasis` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.bis double neft` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.guardpfno` | 0 | 0 | 1 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbmcustrating` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbgattendancemarkerstafftype` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbgattendancehours` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbmday` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbgstafftype` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbmgenderapplicability` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbgleavestatus` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.sysdiagrams` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.saleseinvoice` | 0 | 22 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbmmonth` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbmformtype` | 0 | 0 | 2 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.v_partpaid_total` | 0 | 1 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbmmaritalstatus` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbgofficestafftype` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbm_hr_information_status` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbmdocumenttype` | 0 | 0 | 2 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbgattendancetype` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.flg` | 0 | 1 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.guarddojdob` | 0 | 0 | 2 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.v_rowcount` | 0 | 1 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbmcachemessage` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbgsalaryheadtype` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.j_bills` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.scs` | 0 | 1 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbmyear` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.mobilenumbers` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.dashboard_snapshot_meta` | 0 | 0 | 1 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbmpofiltertype` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbmcommanmaster` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.emailidupdate` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbalertexclude` | 0 | 0 | 1 | 1 | rows≈0, writes=0, reads=0, joins=0; empty |
| -100.0 | `public.smtbmagencytype` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty |
| -105.0 | `public.user_activity_log` | 0 | 0 | 1 | 0 | rows≈0, writes=0, reads=0, joins=1; empty; name looks like log/backup/temp/framework table |
| -108.0 | `public.ai_test_table` | 0 | 0 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty; name looks like log/backup/temp/framework table |
| -108.0 | `public.db_error_log` | 0 | 0 | 1 | 0 | rows≈0, writes=0, reads=0, joins=0; empty; name looks like log/backup/temp/framework table |
| -108.0 | `public.tmp_final_calculations_result` | 0 | 4 | 0 | 0 | rows≈0, writes=0, reads=0, joins=0; empty; name looks like log/backup/temp/framework table |
