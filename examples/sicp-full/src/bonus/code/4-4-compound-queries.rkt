
#lang sicp

;; ===================================================================
;; =========================== ch2 Tools =============================
;; ===================================================================

(define operation-table '())

(define (assoc key records)
  (cond ((null? records) #f)
        ((equal? key (caar records)) (car records))
        (else (assoc key (cdr records)))))

(define (assoc-op key records)
   (cond ((null? records) #f)
         ((equal? key (caar records)) (car records))
         (else (assoc-op key (cdr records)))))

(define (put op type-tags proc)
  (let ((op-list-entry (assoc-op op operation-table)))
    (if op-list-entry
        (let ((proc-list (cadr op-list-entry)))
           (let ((proc-pair-entry (assoc type-tags proc-list)))
             (if proc-pair-entry
                 (set-cdr! proc-pair-entry proc)
                 (set-car! (cdr op-list-entry)
                           (cons (cons type-tags proc) proc-list)))))
        (set! operation-table
              (cons (list op (list (cons type-tags proc)))
                    operation-table)))))

(define (get op type-tags)
  (let ((op-list-entry (assoc-op op operation-table)))
    (if op-list-entry
        (let ((proc-list (cadr op-list-entry)))
          (let ((proc-pair-entry (assoc type-tags proc-list)))
            (if proc-pair-entry
                (cdr proc-pair-entry)
                #f)))
        #f)))

;; ===================================================================
;; =================== ch3 (stream) Tools ============================
;; ===================================================================

(define (stream-car stream)
  (car stream))
(define (stream-cdr stream)
  (force (cdr stream)))

(define (stream-map proc . argstreams)
  (if (stream-null? (car argstreams))
      the-empty-stream
      (cons-stream
       (apply proc (map stream-car argstreams))
       (apply stream-map (cons proc (map stream-cdr argstreams))))))

(define (stream-append s1 s2)
  (if (stream-null? s1)
      s2
      (cons-stream
       (stream-car s1)
       (stream-append (stream-cdr s1) s2))))

(define (stream-append-delayed s1 delayed-s2)
  (if (stream-null? s1)
      (force delayed-s2)
      (cons-stream
       (stream-car s1)
       (stream-append-delayed (stream-cdr s1)
                              delayed-s2))))

(define (interleave-delayed s1 delayed-s2)
  (if (stream-null? s1)
      (force delayed-s2)
      (cons-stream
       (stream-car s1)
       (interleave-delayed
        (force delayed-s2)
        (delay (stream-cdr s1))))))

; singleton-stream
(define (singleton-stream x)
  (cons-stream x the-empty-stream))

(define (stream-for-each proc s)
  (if (not (stream-null? s))
      (begin
        (proc (stream-car s))
        (stream-for-each proc
                         (stream-cdr s)))))

(define (display-stream s)
  (stream-for-each display-line s))

(define (display-line x)
  (newline)
  (display x))


; stream-flatmap
(define (stream-flatmap proc s)
  (flatten-stream (stream-map proc s)))

(define (flatten-stream stream)
  (if (stream-null? stream)
      the-empty-stream
      (interleave-delayed
       (stream-car stream)
       (delay (flatten-stream
               (stream-cdr stream))))))
;; ===================================================================
;; ========================= ch4 Stuff ===============================
;; ===================================================================

; =============== 4.4.4.8
(define (make-binding variable value)
  (cons variable value))
(define (binding-variable binding)
  (car binding))
(define (binding-value binding)
  (cdr binding))
(define (binding-in-frame variable frame)
  (assoc variable frame))
(define (extend variable value frame)
  (cons (make-binding variable value) frame))

; =============== 4.4.4.5
(define THE-ASSERTIONS the-empty-stream)

(define (fetch-assertions pattern frame)
  (if (use-index? pattern)
      (get-indexed-assertions pattern)
      (get-all-assertions)))

(define (get-all-assertions) THE-ASSERTIONS)

(define (get-indexed-assertions pattern)
  (get-stream (index-key-of pattern)
              'assertion-stream))

(define (get-stream key1 key2)
  (let ((s (get key1 key2)))
    (if s s the-empty-stream)))

(define THE-RULES the-empty-stream)

(define (fetch-rules pattern frame)
  (if (use-index? pattern)
      (get-indexed-rules pattern)
      (get-all-rules)))

(define (get-all-rules) THE-RULES)

(define (get-indexed-rules pattern)
  (stream-append
   (get-stream (index-key-of pattern)
               'rule-stream)
   (get-stream '? 'rule-stream)))

(define (add-rule-or-assertion! assertion)
  (if (rule? assertion)
      (add-rule! assertion)
      (add-assertion! assertion)))

(define (add-assertion! assertion)
  (store-assertion-in-index assertion)
  (let ((old-assertions THE-ASSERTIONS))
    (set! THE-ASSERTIONS
          (cons-stream assertion 
                       old-assertions))
    'ok))

(define (add-rule! rule)
  (store-rule-in-index rule)
  (let ((old-rules THE-RULES))
    (set! THE-RULES
          (cons-stream rule old-rules))
    'ok))


(define (store-assertion-in-index assertion)
  (if (indexable? assertion)
      (let ((key (index-key-of assertion)))
        (let ((current-assertion-stream
               (get-stream 
                key 'assertion-stream)))
          (put key
               'assertion-stream
               (cons-stream 
                assertion
                current-assertion-stream))))))

(define (store-rule-in-index rule)
  (let ((pattern (conclusion rule)))
    (if (indexable? pattern)
        (let ((key (index-key-of pattern)))
          (let ((current-rule-stream
                 (get-stream 
                  key 'rule-stream)))
            (put key
                 'rule-stream
                 (cons-stream 
                  rule
                  current-rule-stream)))))))

(define (indexable? pat)
  (or (constant-symbol? (car pat))
      (var? (car pat))))
(define (index-key-of pat)
  (let ((key (car pat)))
    (if (var? key) '? key)))
(define (use-index? pat)
  (constant-symbol? (car pat)))

; =============== 4.4.4.3 ================

(define (find-assertions pattern frame)
  (stream-flatmap
    (lambda (datum)
      (check-an-assertion datum pattern frame))
    (fetch-assertions pattern frame)))
(define (check-an-assertion 
         assertion query-pat query-frame)
  (let ((match-result
         (pattern-match 
          query-pat assertion query-frame)))
    (if (eq? match-result 'failed)
        the-empty-stream
        (singleton-stream match-result))))
(define (pattern-match pat dat frame)
  (cond ((eq? frame 'failed) 'failed)
        ((equal? pat dat) frame)
        ((var? pat) 
         (extend-if-consistent 
          pat dat frame))
        ((and (pair? pat) (pair? dat))
         (pattern-match 
          (cdr pat) 
          (cdr dat)
          (pattern-match
           (car pat) (car dat) frame)))
        (else 'failed)))
(define (extend-if-consistent var dat frame)
  (let ((binding (binding-in-frame var frame)))
    (if binding
        (pattern-match 
         (binding-value binding) dat frame)
        (extend var dat frame))))


;; ======================== 4.4.4.1

;; (define input-prompt  ";;; Query input:")
;; (define output-prompt ";;; Query results:")
;; 
;; (define (query-driver-loop)
;;   (prompt-for-input input-prompt)
;;   (let ((q (query-syntax-process (read))))
;;     (cond ((assertion-to-be-added? q)
;;            (add-rule-or-assertion! 
;;             (add-assertion-body q))
;;            (newline)
;;            (display 
;;             "Assertion added to data base.")
;;            (query-driver-loop))
;;           (else
;;            (newline)
;;            (display output-prompt)
;;            (display-stream
;;             (stream-map
;;              (lambda (frame)
;;                (instantiate
;;                 q
;;                 frame
;;                 (lambda (v f)
;;                   (contract-question-mark v))))
;;              (qeval q (singleton-stream '()))))
;;            (query-driver-loop)))))

(define (run-query input)
  (let ((q (query-syntax-process input)))
    (cond ((assertion-to-be-added? q)
           (add-rule-or-assertion! 
            (add-assertion-body q)))
          (else
           (stream-map
            (lambda (frame)
              (instantiate
               q
               frame
               (lambda (v f)
                 (contract-question-mark v))))
            (qeval q (singleton-stream '())))))))
(define (instantiate
         exp frame unbound-var-handler)
  (define (copy exp)
    (cond ((var? exp)
           (let ((binding
                  (binding-in-frame
                   exp frame)))
             (if binding
                 (copy
                  (binding-value binding))
                 (unbound-var-handler
                  exp frame))))
          ((pair? exp)
           (cons (copy (car exp))
                 (copy (cdr exp))))
          (else exp)))
  (copy exp))

(define (qeval query frame-stream)
  (let ((qproc (get (type query) 'qeval)))
    (if qproc
        (qproc (contents query) frame-stream)
        (simple-query query frame-stream))))

(define (simple-query query-pattern 
                      frame-stream)
  (stream-flatmap
   (lambda (frame)
     (stream-append-delayed
      (find-assertions query-pattern frame)
      (delay 
        (apply-rules query-pattern frame))))
   frame-stream))


;; ======================= 4.4.4.7
(define (type exp)
  (if (pair? exp)
      (car exp)
      (error "Unknown expression TYPE"
             exp)))
(define (tagged-list? exp tag)
  (if (pair? exp)
      (eq? (car exp) tag)
      false))

(define (contents exp)
  (if (pair? exp)
      (cdr exp)
      (error "Unknown expression CONTENTS"
             exp)))

(define (assertion-to-be-added? exp)
  (eq? (type exp) 'assert!))

(define (add-assertion-body exp)
  (car (contents exp)))

(define (empty-conjunction? exps) (null? exps))
(define (first-conjunct exps) (car exps))
(define (rest-conjuncts exps) (cdr exps))
(define (empty-disjunction? exps) (null? exps))
(define (first-disjunct exps) (car exps))
(define (rest-disjuncts exps) (cdr exps))
(define (negated-query exps) (car exps))
(define (predicate exps) (car exps))
(define (args exps) (cdr exps))

(define (rule? statement)
  (tagged-list? statement 'rule))

(define (conclusion rule) (cadr rule))

(define (rule-body rule)
  (if (null? (cddr rule))
      '(always-true)
      (caddr rule)))

(define (query-syntax-process exp)
  (map-over-symbols expand-question-mark exp))

(define (map-over-symbols proc exp)
  (cond ((pair? exp)
         (cons (map-over-symbols
                proc (car exp))
               (map-over-symbols
                proc (cdr exp))))
        ((symbol? exp) (proc exp))
        (else exp)))

(define (expand-question-mark symbol)
  (let ((chars (symbol->string symbol)))
    (if (string=? (substring chars 0 1) "?")
        (list '? (string->symbol
                  (substring
                   chars
                   1
                   (string-length chars))))
        symbol)))

(define (var? exp) (tagged-list? exp '?))
(define (constant-symbol? exp) (symbol? exp))

(define rule-counter 0)

(define (new-rule-application-id)
  (set! rule-counter (+ 1 rule-counter))
  rule-counter)

(define (make-new-variable
         var rule-application-id)
  (cons '? (cons rule-application-id
                 (cdr var))))

(define (contract-question-mark variable)
  (string->symbol
   (string-append "?"
     (if (number? (cadr variable))
         (string-append
          (symbol->string (caddr variable))
          "-"
          (number->string (cadr variable)))
         (symbol->string (cadr variable))))))


;; ======================== 4.4.4.2 Compound Queries
(define user-initial-environment (scheme-report-environment 5))
(define (always-true ignore frame-stream)
  frame-stream)
(put 'always-true 'qeval always-true)

(define (execute exp)
  (apply (eval (predicate exp) 
               user-initial-environment)
         (args exp)))

(define (lisp-value call frame-stream)
  (stream-flatmap
   (lambda (frame)
     (if (execute
          (instantiate
           call
           frame
           (lambda (v f)
             (error 
              "Unknown pat var: LISP-VALUE" 
              v))))
         (singleton-stream frame)
         the-empty-stream))
   frame-stream))
(put 'lisp-value 'qeval lisp-value)

(define (negate operands frame-stream)
  (stream-flatmap
   (lambda (frame)
     (if (stream-null?
          (qeval (negated-query operands)
                 (singleton-stream frame)))
         (singleton-stream frame)
         the-empty-stream))
   frame-stream))
(put 'not 'qeval negate)

(define (conjoin conjuncts frame-stream)
  (if (empty-conjunction? conjuncts)
      frame-stream
      (conjoin (rest-conjuncts conjuncts)
               (qeval
                (first-conjunct conjuncts)
                frame-stream))))
(put 'and 'qeval conjoin)

(define (disjoin disjuncts frame-stream)
  (if (empty-disjunction? disjuncts)
      the-empty-stream
      (interleave-delayed
       (qeval (first-disjunct disjuncts)
              frame-stream)
       (delay (disjoin
               (rest-disjuncts disjuncts)
               frame-stream)))))
(put 'or 'qeval disjoin)

; placeholder for rules
(define (apply-rules query-pattern frame) the-empty-stream)

;; Relevant Code
(define (build-database)
  (begin 
    (add-assertion! '(address (Bitdiddle Ben)
                              (Slumerville (Ridge Road) 10)))
    (add-assertion! '(job (Bitdiddle Ben) (computer wizard)))
    (add-assertion! '(salary (Bitdiddle Ben) 60000))
    (add-assertion! '(address (Hacker Alyssa P)
                              (Cambridge (Mass Ave) 78)))
    (add-assertion! '(job (Hacker Alyssa P) (computer programmer)))
    (add-assertion! '(salary (Hacker Alyssa P) 40000))
    (add-assertion! '(supervisor (Hacker Alyssa P) (Bitdiddle Ben)))
    (add-assertion! '(address (Fect Cy D)
                              (Cambridge (Ames Street) 3)))
    (add-assertion! '(job (Fect Cy D) (computer programmer)))
    (add-assertion! '(salary (Fect Cy D) 35000))
    (add-assertion! '(supervisor (Fect Cy D) (Bitdiddle Ben)))
    (add-assertion! '(address (Tweakit Lem E)
                              (Boston (Bay State Road) 22)))
    (add-assertion! '(job (Tweakit Lem E) (computer technician)))
    (add-assertion! '(salary (Tweakit Lem E) 25000))
    (add-assertion! '(supervisor (Tweakit Lem E) (Bitdiddle Ben)))
    (add-assertion! '(address (Reasoner Louis)
                              (Slumerville (Pine Tree Road) 80)))
    (add-assertion! '(job (Reasoner Louis)
                          (computer programmer trainee)))
    (add-assertion! '(salary (Reasoner Louis) 30000))
    (add-assertion! '(supervisor (Reasoner Louis)
                                 (Hacker Alyssa P)))
    (add-assertion! '(supervisor (Bitdiddle Ben) (Warbucks Oliver)))
    (add-assertion! '(address (Warbucks Oliver)
                              (Swellesley (Top Heap Road))))
    (add-assertion! '(job (Warbucks Oliver)
                          (administration big wheel)))
    (add-assertion! '(salary (Warbucks Oliver) 150000))
    (add-assertion! '(address (Scrooge Eben)
                              (Weston (Shady Lane) 10)))
    (add-assertion! '(job (Scrooge Eben)
                          (accounting chief accountant)))
    (add-assertion! '(salary (Scrooge Eben) 75000))
    (add-assertion! '(supervisor (Scrooge Eben) (Warbucks Oliver)))
    (add-assertion! '(address (Cratchet Robert)
                              (Allston (N Harvard Street) 16)))
    (add-assertion! '(job (Cratchet Robert) (accounting scrivener)))
    (add-assertion! '(salary (Cratchet Robert) 18000))
    (add-assertion! '(supervisor (Cratchet Robert) (Scrooge Eben)))
    (add-assertion! '(address (Aull DeWitt)
                              (Slumerville (Onion Square) 5)))
    (add-assertion! '(job (Aull DeWitt) (administration secretary)))
    (add-assertion! '(salary (Aull DeWitt) 25000))
    (add-assertion! '(supervisor (Aull DeWitt) (Warbucks Oliver)))))

(build-database)

(display-line "Query (and (supervisor ?x (Bitdiddle Ben))
    (address ?x ?address)):")
(display-stream
 (run-query 
  '(and (supervisor ?x (Bitdiddle Ben))
    (address ?x ?address))))
(newline)

(display-line "Query (and (supervisor ?person ?super)
     (job ?super (?division . ?type))
     (not (job ?super (computer . ?type)))):")
(display-stream
 (run-query '(and (supervisor ?person ?super)
     (job ?super (?division . ?type))
     (not (job ?super (computer . ?type))))))
(newline)

(display-line "Query (and (salary (Bitdiddle Ben) ?benamount)
     (salary ?person ?personamount)
     (lisp-value < ?personamount ?benamount)):")
(display-stream
 (run-query '(and (salary (Bitdiddle Ben) ?benamount)
     (salary ?person ?personamount)
     (lisp-value < ?personamount ?benamount))))
(newline)
