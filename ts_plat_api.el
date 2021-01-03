
{---------------------------------------------------------------------------------------------------
IDENTIFICATION
==============
Name: 			TS Data API using GlobalDictionary
Type:			Indicator
TS Version:		10 Build 40 or later

---------------------------------------------------------------------------------------------------
DOCUMENTATION
=============
This indicator is based on the original _Python GlobalDictionary created by JohnR from Tradestation.

It tries to mimic Web API using the GlobalDictionary approach. It is work in progress, use it at your
own risk! There could be issues related to COM objects in memory, messsages and abusing the concept :D.

It is supposed to be accompanied by a client created in python and executing charting.py

For updates please check the Github repository https://github.com/ebucis/TS_PLAT_API.git

---------------------------------------------------------------------------------------------------
}

using elsystem;
using elsystem.collections;
using elsystem.drawing;
using  tsdata.marketdata;
using tsdata.common;

variables:
	intrabarpersist Counter(0),
	GlobalDictionary GD(null);
	
var: 
	Dictionary interval_chartTypes(null),
	Dictionary interval_Types(null),
	Dictionary interval_Range_Types(null),
	Dictionary psps(null);

method void init_Enums()
Begin
	//Interval
		//IntervalChartTypes
		interval_chartTypes = Dictionary.Create();
		interval_chartTypes["BARS"] = DataChartType.Bars;
		interval_chartTypes["VOLUME"] = DataChartType.Volume;
	
		//IntervalType
		interval_Types = Dictionary.Create();
		interval_Types["TICKS"] = DataIntervalType.Ticks;
		interval_Types["MINUTES"] = DataIntervalType.Minutes;
		interval_Types["DAILY"] = DataIntervalType.Daily;
		interval_Types["WEEKLY"] = DataIntervalType.Weekly;	
		interval_Types["MONTHLY"] = DataIntervalType.Monthly;
		interval_Types["SECONDS"] = DataIntervalType.Seconds;
		
			
		
		//RangeType
		interval_Range_Types = Dictionary.Create();
		interval_Range_Types["BARS"] = DataRangeType.Bars;
		interval_Range_Types["DATE"] = DataRangeType.Date;
		interval_Range_Types["DAYS"] = DataRangeType.Days;
		interval_Range_Types["MONTHS"] = DataRangeType.Months;
		interval_Range_Types["WEEKS"] = DataRangeType.Weeks;
		interval_Range_Types["YEARS"] = DataRangeType.Years;
End;



method int getEnumByName(Dictionary dict, string enumName)
Begin
	enumName = Upperstr(enumName);
	if dict.Contains(enumName) Then
		return dict[enumName] astype int;
	return -1;	
End;	

//returns a request key
method string getDictionaryKey(string symb, string chart_type, string bar_type, string bar_interval, string range_type, string range_value)
var: string res;
Begin
	res = symb+"_"+chart_type+"_"+bar_type+"_"+bar_interval+"_"+range_type+"_"+range_value;
	return res; 
End;	



	{status_bitmap = 
		0: 'NEW',
		1: 'REAL_TIME_DATA',
		2: 'HISTORICAL_DATA',
		3: 'STANDARD_CLOSE',
		4: 'END_OF_SESSION_CLOSE',
		5: 'UPDATE_CORPACTION',
		6: 'UPDATE_CORRECTION',
		7: 'ANALYSIS_BAR',
		8: 'EXTENDED_BAR',
		19: 'PREV_DAY_CORRECTION',
		23: 'AFTER_MARKET_CORRECTION',
		24: 'PHANTOM_BAR',
		25: 'EMPTY_BAR',
		26: 'BACKFILL_DATA',
		27: 'ARCHIVE_DATA',
		28: 'GHOST_BAR',
		29: 'END_OF_HISTORY_STREAM',
	}
	
//this is an attempt to get the bar status as it is done in the web api...work in progress	
method int getBarStatus(int barno, PriceSeries dta, tsdata.marketdata.PriceSeriesProvider psp, PriceSeriesUpdatedEventArgs args)
var: int res, int temp;
Begin
	//if it is from an update event, usually real time
	if args <> Null Then
	Begin
		if args.IsRealtimeBar Then
			res = res or 2;
		if args.IsEndOfSession Then
			res = res or 16;
			
		if args.IsEmptyBar Then
		Begin
			Value1 =Power(2, 25);
			temp = Intportion(Value1);
			res = res or temp;
		End;	
		if args.IsGhostBar Then
		Begin
			Value1 =Power(2, 29);
			temp = Intportion(Value1);
			res = res or temp;
		End;
		
		{
			args.Reason
			Public property  BarClose 
			2
 			
			Public property  BarInitialUpdate 
			3
 			
			Public property  BarOpen 
			1
 			
			Public property  BarUpdate 
			0
 			
		}	
		if args.Reason = 0 Then
			res = res or 1
		else if args.Reason = 2 Then
			res = res or 8;
	End
	Else
		//if history 
		if barno < psp.Count then
		Begin
			res = res or 1 or 4 or 8;
		End
		Else
		//"realtime" not from event
		Begin
			//call it end of history
			Value1 =Power(2, 29);
			
			temp = Intportion(Value1);
			res = res or 2 or temp;
			
			//just in case we don't have any real time in session
			if dta.LastBarIsClosed Then
				res = res or 8;
			if not dta.LastBarIsOpen Then
				res = res or 4;
			
			//just in case we don't have any real time in session
			if dta.LastBarIsSessionClosed Then
				res = res or 16;
				
		End;
	return res;
End;


const: string MDYHMSFormat("%m/%d/%y %H:%M:%S");
//writing the data to the global dictionary
method void WriteData(Dictionary TL, int barno, tsdata.marketdata.PriceSeriesProvider psp, PriceSeriesUpdatedEventArgs args)
variables:
	 string str, int volu, int vold, int vol, PriceSeries dta, string key, Dictionary msg, string json, int idx,
	DateTime dt;
begin
	idx = psp.Count - barno;
	Begin
		dta = psp.Data;
		TL["BarNumber"] = barno; 
		dt = dta.Time[idx];
 		TL["TimeStamp"] = dt; 
 		TL["DateTime"] = dta.Time[idx].Format(MDYHMSFormat); 
 		TL["Status"] = getBarStatus(barno, dta, psp, args); 
 		
 		TL["Close"] = dta.Close[idx]; 
 		TL["Open"] = dta.Open[idx]; 
 		TL["High"] = dta.High[idx]; 
 		TL["Low"] = dta.Low[idx]; 
 		
 		TL["UpTicks"] = dta.TicksUp[idx]; 
 		TL["DownTicks"] = dta.TicksDown[idx]; 
 		TL["UnchangedTicks"] = 0.0;//dta.TicksUnchanged[idx]; 
 		TL["TotalTicks"] = dta.Ticks[idx];
		
 		TL["UpVolume"] = dta.VolumeUp[idx]; 
 		TL["DownVolume"] = dta.VolumeDown[idx]; 
 		TL["UnchangedVolume"] = 0.0;// dta.VolumeUnchanged[idx]; 
 		TL["TotalVolume"] = dta.Volume[idx]; 
		
 		TL["OpenInterest"] = dta.OpenInterest[idx]; 
 		
 		key = psp.Name;
 		
 		GD[key] = TL;
 	End;	
end;

var: intrabarpersist Dictionary tl(null);
//on update
method void psp_Updated( elsystem.Object sender, tsdata.marketdata.PriceSeriesUpdatedEventArgs args) 
var:
	PriceSeriesProvider psp;
Begin
	if sender <> null Then
	Begin
		psp = sender astype PriceSeriesProvider;
		WriteData(tl, psp.Count, psp, args);
	End;
End;

//to avoid ts to complain in large datasets
[InfiniteLoopDetect = FALSE]
method void write_psp(PriceSeriesProvider psp)
var: int bno, int cnt;
Begin
	cnt = psp.Count;
	for bno = 1 to cnt
	Begin
		WriteData(tl, bno, psp, null);
	End;
	//less efficient cycle in case neew bars kept coming (not sure if it is really multithreaded)
	if cnt < psp.Count Then
	Begin
		bno = cnt;
		cnt = psp.Count;
		while bno < cnt
		Begin
			WriteData(tl, bno, psp, null);
			cnt = psp.Count;
			bno+=1;
		End;
	End;	
End;

//on load
method void psp_StateChanged( elsystem.Object sender, tsdata.common.StateChangedEventArgs args ) 
var: tsdata.common.DataState ostr, PriceSeriesProvider psp;
begin
	ostr = args.NewState;
	if (ostr = DataState.loaded) then 
	Begin
		psp = sender astype PriceSeriesProvider;
		write_psp(psp);
		psp.Updated+=psp_Updated;
	End;	
end;

//data request object
method PriceSeriesProvider createPSP(string name, string symb, int chart_type,int bar_type, int bar_interval, int range_type, int range_value)
var: PriceSeriesProvider psp, int cnt, string rn;
Begin
	try
		psp = new tsdata.marketdata.PriceSeriesProvider;
		psp.Name = name;
		psp.Symbol = symb;
		psp.SessionName = "Crypto";
		psp.UseNaturalHours = false;
		psp.Interval.ChartType =chart_type;
		psp.Interval.IntervalType = bar_type;
		psp.Interval.IntervalSpan = bar_interval;
		psp.Interval.Name = numtostr(chart_type, 0)+"_"+Numtostr(bar_type, 0)+"_"+Numtostr(bar_interval, 0);
		psp.Range.Type = range_type;
		switch (range_type)
		Begin
		
			case tsdata.marketdata.DataRangeType.Bars:
				psp.Range.Bars = range_value;
			case tsdata.marketdata.DataRangeType.Days:
				psp.Range.Days = range_value;	
			case tsdata.marketdata.DataRangeType.Months:
				psp.Range.Months = range_value;	
			case tsdata.marketdata.DataRangeType.Weeks:
				psp.Range.Weeks = range_value;	
			case tsdata.marketdata.DataRangeType.Years:
				psp.Range.Years = range_value;				
			default:
				throw InvalidOperationException.Create (range_type.ToString()+" not supported ");	
		End;
		//psp.Range. Months = range_value;
		rn = Numtostr(range_type, 0) + Numtostr(range_value, 0);
		psp.Range.Name = rn;
		psp.IncludeVolumeInfo = true;
		psp.IncludeTicksInfo = true;
		psp.UseNaturalHours = false;
		psp.Realtime = true;
		psp.TimeZone = tsdata.common.TimeZone.local;
		psp.Load = true;
		psp.StateChanged+=psp_StateChanged;
		//after we do history...
		//psp.Updated+=psp_Updated;
{		psp.LoadProvider();
		cnt = psp.Count;}
	Catch (Exception ex)
		Clearprintlog;
		print(ex.Message);
		throw ex;
	End;	
	
	return psp;
End;


// Creates GlobalDictionary
method void CreateGlobalDictionary()
begin
	GD = GlobalDictionary.Create(true, "TS_PLAT_API");
	GD.Cleared += GD_Cleared;
	GD.ItemAdded += GD_ItemAdded;
	GD.ItemChanged += GD_ItemChanged;
end;


// Destroys GlobalDictionary
method void DestroyGlobalDictionary()
begin
	GD = null;
end;

// Event handler when GlobalDictionary is cleared  
method void GD_Cleared ( elsystem.Object sender, elsystem.collections.ItemProcessedEventArgs args )
begin
	Print( "*GD_Cleared event*" );
end;


{	
	request_data = 
			'id': key, 
			'symbol': symbol, 
			'chart_type':chart_type, 
			'interval_type': interval_type, 
			'interval_value': interval_value, 
			'range_type' : range_type,
			'range_value' : range_value
}	

//parse request and issue price series provider	
method void _process_request(Dictionary request)
var: string smb, DataChartType chart_type, DataIntervalType interval_type, DataRangeType range_type, int range_value, int interval_value,
	tsdata.marketdata.PriceSeriesProvider psp, string key, string str, object obj, string name; 
Begin
	key = request["id"] astype string;
	
	if psps[key] <> null then
	Begin
		psp = psps[key] astype tsdata.marketdata.PriceSeriesProvider;
		if psp.State = DataState.loaded Then
		Begin
			write_psp(psp);
		End;
	End
	Else
	Begin
		smb = request["symbol"] astype string;
		str = request["chart_type"] astype string;
		chart_type = interval_chartTypes[str] astype DataChartType;
		str = request["interval_type"] astype string;
		interval_type = interval_types[str] astype DataIntervalType;
		str = request["range_type"] astype string;
		range_type = interval_Range_Types[str] astype DataRangeType;
		range_value = request["range_value"] astype int;
		interval_value = request["interval_value"] astype int;
		name = request["id"] astype string;
		
		psp = createPSP(name, smb, chart_type, interval_type, interval_value, range_type, range_value);

		psps[key] = psp;
	End;	
End;

// Event handler when item is added to GlobalDictionary
method void GD_ItemAdded( elsystem.Object sender, elsystem.collections.ItemProcessedEventArgs args )
var: Dictionary message;
begin
	//we only care about client request
	if args.Key = "request" Then
	Begin
		if args.Value Istype Dictionary Then
		Begin
			_process_request(args.Value astype Dictionary);
		End;
	End;
	//Print( String.Format( "*GD_ItemAdded event* Key {0} added with value of {1} -> New size: {2}", args.Key, args.Value, GD.Count ) );
end;


// Event handler when GlobalDictionary item is changed
method void GD_ItemChanged( elsystem.Object sender, elsystem.collections.ItemProcessedEventArgs args )
begin
	//we only care about client request
	if args.Key = "request" Then
	Begin
		if args.Value Istype Dictionary Then
		Begin
			_process_request(args.Value astype Dictionary);
		End;
	End;
end;

// Initialize
once
begin
	init_Enums();
	psps = Dictionary.Create();
	CreateGlobalDictionary();
	tl = Dictionary.Create();
	if GD["Singleton"] <> null Then
	Begin
		Raiseruntimeerror("TS PLAT API should run only once");
	End;
	GD["Singleton"] = True;	
end;
