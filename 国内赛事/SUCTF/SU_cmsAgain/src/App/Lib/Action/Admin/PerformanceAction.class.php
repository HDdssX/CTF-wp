<?php
/**
 * Youdian Content Management System
 * Copyright (C) YoudianSoft Co.,Ltd (http://www.youdiancms.com). All rights reserved.
 */
class PerformanceAction extends AdminBaseAction{
	//友情链接
	function index(){
		header("Content-Type:text/html; charset=utf-8");
		$CurrentYear = (int)date('Y');
		$CurrentMonth = (int)date('m');
		$options['Parameter'] = array(
			'CustomerID' => isset($_REQUEST['CustomerID']) ? (int)$_REQUEST['CustomerID'] : -1,
			'ProjectType' => isset($_REQUEST['ProjectType']) ? (int)$_REQUEST['ProjectType'] : -1,
			'OperatorID' =>  isset($_REQUEST['OperatorID']) ? (int)$_REQUEST['OperatorID'] : -1,
			'Year'=>isset($_REQUEST['Year']) ? (int)$_REQUEST['Year'] : $CurrentYear,
			'Month'=>isset($_REQUEST['Month']) ? (int)$_REQUEST['Month'] : $CurrentMonth,
			'NeedInvoice' => isset($_REQUEST['NeedInvoice']) ? $_REQUEST['NeedInvoice'] : -1,
			'PayTypeID' => isset($_REQUEST['PayTypeID']) ? (int)$_REQUEST['PayTypeID'] : -1,
		);
		//获取用户信息==================================
		$ma = D('Admin/Authorize');
		$CustomerData = $ma->getCustomerData();
		$this->assign('CustomerData', $CustomerData);
		
		$OperatorData = $ma->getOperatorData();
		$this->assign('OperatorData', $OperatorData);
		
		$Type = $this->getProjectType();
		$this->assign('Type', $Type);
		
		$PayType = $this->getPayType();
		$this->assign('PayType', $PayType);
		//==========================================
		
		$Parameter = $options['Parameter'];
		$m = D('Admin/Performance');
		import("ORG.Util.Page");
		$TotalPage = $m->getPerformanceCount( $Parameter );
		$PageSize = isset($options['PageSize']) ? $options['PageSize'] : $this->AdminPageSize;
		$Page = new Page($TotalPage, $PageSize);
		$Page->rollPage = $this->AdminRollPage;
		//获取参数
		if( !empty( $Parameter ) ){
			$p = '';
			foreach ($Parameter as $k=>$v){
				$p .= "&{$k}={$v}";
				$this->assign($k, $v); //赋值模板变量
			}
			$Page->parameter = $p;
		}
		$data = $m->getPerformance($Page->firstRow, $Page->listRows, $Parameter );
		if(!empty($data)){
			$n = is_array($data) ? count($data) : 0;
			$mm = D('Admin/Member');
			for($i = 0; $i < $n; $i++){
				$CustomerID = (int)$data[$i]['CustomerID'];
				if( $CustomerID > 0 ){
					$CustomerName = $mm->where("MemberID=$CustomerID")->getField('MemberRealName');
					$data[$i]['CustomerName'] = $CustomerName;
				}
				
				$OperatorID = (int)$data[$i]['OperatorID'];
				if( $OperatorID > 0 ){
					$OperatorName = $mm->where("MemberID=$OperatorID")->getField('MemberRealName');
					$data[$i]['OperatorName'] = $OperatorName;
				}
				
				$typeid = $data[$i]['ProjectType'];
				$payid = $data[$i]['PayType'];
				$data[$i]['ProjectTypeName'] = $Type[ $typeid ]['ProjectTypeName'];
				$data[$i]['PayTypeName'] = $PayType[ $payid ]['PayTypeName'];
			}
		}
        $YearSpan = array();
		for($i = 2012; $i<=$CurrentYear; $i++){
			$YearSpan[]['Year'] = $i;
		}
		$this->assign('YearSpan', $YearSpan);
		
		$ShowPage = $Page->show();
		$TotalFee = $m->getTotalFee($Parameter);
		$this->assign('TotalFee', $TotalFee);
		
		if( $_REQUEST['CustomerID'] > 0 ){
			$AgentFee = $m->getAgentFee( $_REQUEST['CustomerID'] );
			$TemplateFee = $m->getTemplateFee( $_REQUEST['CustomerID'] );
			$LeftFee = $AgentFee - $TemplateFee;
			$this->assign('AgentFee', $AgentFee);
			$this->assign('TemplateFee', $TemplateFee);
			$this->assign('LeftFee', $LeftFee);
		}
		
		$this->assign('NowPage', $Page->getNowPage()); //当前页码
		$this->assign('Page', $ShowPage); //分页条
		$this->assign('Data', $data);
		$this->display();
	}
	
	//删除、批量删除
	function del(){
		$options['Parameter'] = array(
				'CustomerID' => isset($_REQUEST['CustomerID']) ? $_REQUEST['CustomerID'] : -1,
				'ProjectType' => isset($_REQUEST['ProjectType']) ? $_REQUEST['ProjectType'] : -1,
				'OperatorID' =>  isset($_REQUEST['OperatorID']) ? $_REQUEST['OperatorID'] : -1,
				'p'=>$_REQUEST["NowPage"],
		);
		$this->opDel( $options );
	}
	
	//获取项目类别
	private function getProjectType(){
		$m = D('Admin/Performance');
		$data = $m->getProjectType();
		return $data;
	}
	
	private function getPayType(){
		$m = D('Admin/Performance');
		$data = $m->getPayType();
		return $data;
	}

	function add(){
		$options = array();
		$this->assign('Type', $this->getProjectType() );
		//获取用户信息==================================
		$ma = D('Admin/Authorize');
		$CustomerData = $ma->getCustomerData();
		$this->assign('CustomerData', $CustomerData);
		
		$PayType = $this->getPayType();
		$this->assign('PayType', $PayType);
		//==========================================
		
		//默认数据
		$Data = array('ProjectFee'=>0, 'ProjectType'=>1, 'AddTime'=>date('Y-m-d H:i:s'), 'PayType'=>1
				,'NeedInvoice'=>0, 'TemplateCount'=>0, 'IsAuthorize'=>1, 'Host'=>'' );
		$this->assign('Data', $Data);
		
		$this->opAdd( false, $options );
	}
	
	function saveAdd(){
		header("Content-Type:text/html; charset=utf-8");
		$this->_checkPost( $_POST );
		$m = D('Admin/Performance');
		if( $_POST['ProjectType'] == 7){
			//需要判断模板编号是否存在
			if( $m->pcTemplateExist($_POST['PcNumber'], $_POST['CustomerID']) ){
				$this->ajaxReturn(null, "电脑模板编号{$_POST['PcNumber']}已经存在" , 0);
			}
			if( $m->wapTemplateExist($_POST['WapNumber'], $_POST['CustomerID']) ){
				$this->ajaxReturn(null, "手机模板编号{$_POST['WapNumber']}已经存在" , 0);
			}
		}
		if( $m->create() ){
			$m->OperatorID = (int)session('AdminMemberID');
			if($m->add()){
				$this->ajaxReturn(null, '添加成功!' , 1);
			}else{
				$this->ajaxReturn(null, '添加失败!' , 0);
			}
		}else{
			$this->ajaxReturn(null, $m->getError() , 0);
		}
	}
	
	function modify(){
		$options = array();
		$this->assign('Type', $this->getProjectType() );
		//获取用户信息==================================
		$ma = D('Admin/Authorize');
		$CustomerData = $ma->getCustomerData();
		$this->assign('CustomerData', $CustomerData);
		
		$PayType = $this->getPayType();
		$this->assign('PayType', $PayType);
		//==========================================
		$this->opModify(false, $options);
	}
	
	function saveModify(){
		header("Content-Type:text/html; charset=utf-8");
		$this->_checkPost( $_POST );
		$b = D('Admin/Performance');
		if( $b->create() ){
			if($b->save() === false){
				$this->ajaxReturn(null, '修改失败!' , 0);
			}else{
				$this->ajaxReturn(null, '修改成功!' , 1);
			}
		}else{
			$this->ajaxReturn(null, $b->getError() , 0);
		}
	}
	
	//检查提交参数
	private function _checkPost($p){
		if( empty($p['ProjectName']) ){
			$this->ajaxReturn(null, '项目名称不能为空' , 0);
		}
	
		if( $p['ProjectType'] != 7  ){ //当登记项目时，不需要判断项目费用
			if( !is_numeric($p['ProjectFee'] ) || $p['ProjectFee'] <= 0 ){
				$this->ajaxReturn(null, '项目费用必须大于0' , 0);
			}
		}
	}
	
	function getInvoiceInfo(){
		header("Content-Type:text/html; charset=utf-8");
		$m = D('Admin/Member');
		$where['MemberID'] = intval($_REQUEST['CustomerID']);
		$where['InviterID'] = (int)session('MemberID');
		$m->field('MemberRealName,MemberName,MemberAddress,MemberMobile');
		$data = $m->where($where)->find();
		if( !empty($data) ){
			$this->ajaxReturn($data, '获取成功!' , 1);
		}else{
			$this->ajaxReturn(null, $m->getError() , 0);
		}
	}
	
	//数据统计
	function stat(){
		header("Content-Type:text/html; charset=utf-8");
		$CurrentYear = (int)date('Y');
		$CurrentMonth = (int)date('m');
		$StatType = isset($_REQUEST['StatType']) ? $_REQUEST['StatType'] : 1;
		$Year = isset($_REQUEST['year']) ? $_REQUEST['year'] : $CurrentYear;
		$m = D('Admin/Performance');
        $data = array();
		$Total = array();
		switch ($StatType){
			case 1: //按业务员统计业绩
				$data = $m->statPerformanceByMember($Year);
				if( !empty($data)){
					$n = is_array($data) ? count($data) : 0;
					for($i = 0; $i < $n; $i++){
						$r = $m->statPerformanceByMonth($Year);
						for($j = 1; $j<=12 ; $j++){
							$k =$data[$i]['OperatorID'].$j;
							$data[$i]['M'.$j] = isset( $r[$k] ) ? $r[$k] : 0;
							$Total['M'.$j] += $data[$i]['M'.$j];
						}
						$Total['Total'] += $data[$i]['Total'];
					}
				}
				$this->assign("HeaderTitle1", '业务员');
				$this->assign("HeaderTitle2", '业绩总计');
				break;
			case 2: //按项目类型统计业绩
				$ProjectTypeData = $m->getProjectType();
				$data = $m->statPerformanceByProjectType($Year);
				if( !empty($data)){
					$n = is_array($data) ? count($data) : 0;
					for($i = 0; $i < $n; $i++){
						$r = $m->statProjectPerformanceByMonth($Year);
						for($j = 1; $j<=12 ; $j++){
							$k =$data[$i]['ProjectType'].$j;
							$data[$i]['M'.$j] = isset( $r[$k] ) ? $r[$k] : 0;
							$Total['M'.$j] += $data[$i]['M'.$j];
						}
						//为了统一显示使用MemberRealName 代替ProjectType
						$data[$i]['MemberRealName'] = $ProjectTypeData[ $data[$i]['ProjectType'] ]['ProjectTypeName'];
						$Total['Total'] += $data[$i]['Total'];
					}
				}
				$this->assign("HeaderTitle1", '项目类型');
				$this->assign("HeaderTitle2", '业绩总计');
				break;
			case 3: //模板使用量统计
				$data = $m->statTemplate($Year);
				if( !empty($data)){
					$n = is_array($data) ? count($data) : 0;
					$r = $m->statTemplateByYear();
					for($i = 0; $i < $n; $i++){
						for($j = 2014; $j<=$CurrentYear ; $j++){
							$k = $data[$i]['PcNumber'].$j;
							$data[$i]['Y'.$j] = isset( $r[$k] ) ? $r[$k] : 0;
							$Total['Y'.$j] += $data[$i]['Y'.$j];
						}
						$Total['Total'] += $data[$i]['Total'];
					}
				}
				break;
			case 4: //按业务员统计工资
				$data = $m->statSalaryByMember($Year);
				if( !empty($data)){
					$n = is_array($data) ? count($data) : 0;
					for($i = 0; $i < $n; $i++){
						$r = $m->statSalaryByMonth($Year);
						for($j = 1; $j<=12 ; $j++){
							$k =$data[$i]['OperatorID'].$j;
							$data[$i]['M'.$j] = isset( $r[$k] ) ? $r[$k] : 0;
							$Total['M'.$j] += $data[$i]['M'.$j];
						}
						$Total['Total'] += $data[$i]['Total'];
					}
				}
				$this->assign("HeaderTitle1", '业务员');
				$this->assign("HeaderTitle2", '工资总计');
				break;
			case 5: //按付款方式统计业绩
				$PayTypeData = $m->getPayType();
				$data = $m->statPerformanceByPayType($Year);
				if( !empty($data)){
					$n = is_array($data) ? count($data) : 0;
					for($i = 0; $i < $n; $i++){
						$r = $m->statPayTypePerformanceByMonth($Year);
						for($j = 1; $j<=12 ; $j++){
							$k =$data[$i]['PayType'].$j;
							$data[$i]['M'.$j] = isset( $r[$k] ) ? $r[$k] : 0;
							$Total['M'.$j] += $data[$i]['M'.$j];
						}
						//为了统一显示使用MemberRealName 代替ProjectType
						$data[$i]['MemberRealName'] = $PayTypeData[ $data[$i]['PayType'] ]['PayTypeName'];
						$Total['Total'] += $data[$i]['Total'];
					}
				}
				$this->assign("HeaderTitle1", '付款方式');
				$this->assign("HeaderTitle2", '业绩总计');
				break;
			case 6: //按分组统计客户数
				$data = $m->statCustomerByMemberGroup($Year);
				if( !empty($data)){
					$n = is_array($data) ? count($data) : 0;
					for($i = 0; $i < $n; $i++){
						$r = $m->statCustomerByMemberGroupMonth($Year);
						for($j = 1; $j<=12 ; $j++){
							$k =$data[$i]['MemberGroupID'].$j;
							$data[$i]['M'.$j] = isset( $r[$k] ) ? $r[$k] : 0;
							$Total['M'.$j] += $data[$i]['M'.$j];
						}
						//为了统一显示使用MemberRealName
						$data[$i]['MemberRealName'] = $data[$i]['MemberGroupName'];
						$Total['Total'] += $data[$i]['Total'];
					}
				}
				$this->assign("HeaderTitle1", '分组');
				$this->assign("HeaderTitle2", '用户数总计');
				break;
			case 7: //按省份统计代理数
				$data = $m->statAgentByProvince($Year);
				if( !empty($data)){
					$n = is_array($data) ? count($data) : 0;
					for($i = 0; $i < $n; $i++){
						$r = $m->statAgentByProvinceMonth($Year);
						for($j = 1; $j<=12 ; $j++){
							$k =$data[$i]['Province'].$j;
							$data[$i]['M'.$j] = isset( $r[$k] ) ? $r[$k] : 0;
							$Total['M'.$j] += $data[$i]['M'.$j];
						}
						$data[$i]['MemberRealName'] = $data[$i]['AreaName'];
						$Total['Total'] += $data[$i]['Total'];
					}
				}
				$this->assign("HeaderTitle1", '省份');
				$this->assign("HeaderTitle2", '代理数总计');
				break;
			case 8: //按省份统计总客户数
				$data = $m->statCustomerByProvince($Year);
				if( !empty($data)){
					$n = is_array($data) ? count($data) : 0;
					for($i = 0; $i < $n; $i++){
						$r = $m->statCustomerByProvinceMonth($Year);
						for($j = 1; $j<=12 ; $j++){
							$k =$data[$i]['Province'].$j;
							$data[$i]['M'.$j] = isset( $r[$k] ) ? $r[$k] : 0;
							$Total['M'.$j] += $data[$i]['M'.$j];
						}
						$data[$i]['MemberRealName'] = $data[$i]['AreaName'];
						$Total['Total'] += $data[$i]['Total'];
					}
				}
				$this->assign("HeaderTitle1", '省份');
				$this->assign("HeaderTitle2", '客户数总计');
				break;
		}
        $YearSpan = array();
		for($i = 2012; $i<=$CurrentYear; $i++){
			$YearSpan[]['Year'] = $i;
		}
		$this->assign('YearSpan', $YearSpan);
		$this->assign('Year', $Year);
		$this->assign('CurrentYear', $CurrentYear);
		$this->assign('CurrentMonth', $CurrentMonth);
		$this->assign('StatType', $StatType);
		$this->assign('Total', $Total);
		$this->assign('Data', $data);
		$this->display();
	}
}