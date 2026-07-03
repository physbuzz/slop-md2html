data = {1, 1, 1,
   2, 1, 1,
   3, 1, 2,
   4, 2, 14,
   5, 8, 156,
   6, 32, 6426,
   7, 124, 46777,
   8, 579, 965044,
   9, 3073, 23825059};
nvals = data[[1 ;; ;; 3]];
t1 = data[[2 ;; ;; 3]]/10^6;
t2 = data[[3 ;; ;; 3]]/10^6;
f1[n_] = 
  Exp[(a Log[n!] + b)] /. 
   FindFit[Thread[{nvals, Log[t1]}], a Log[n!] + b, {a, b}, n];
f2[n_] = 
  Exp[(a Log[n^n] + b)] /. 
   FindFit[Thread[{nvals, Log[t2]}], a Log[n^n] + b, {a, b}, n];
Show[ListLogPlot[{t1, t2}, AxesLabel -> {"n", "t (s)"}, 
  PlotLegends -> {"Orig Timing", "Louis's Timing"}], 
 LogPlot[{f1[n], f2[n]}, {n, 1, Max[nvals]}, 
  PlotLegends -> {"n! fit", "\!\(\*SuperscriptBox[\(n\), \(n\)]\) fit"},
   PlotStyle -> {Directive[Thin, Blue, Dashed], 
    Directive[Thin, Orange, Dashed]}]]
