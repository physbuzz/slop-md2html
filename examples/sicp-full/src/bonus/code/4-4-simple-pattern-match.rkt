#lang sicp

(define (tagged-list? exp tag) (and (pair? exp) (eq? (car exp) tag)))
(define (var? exp) (tagged-list? exp '?))
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
;ch2 assoc
(define (assoc key records)
  (cond ((null? records) #f)
        ((equal? key (caar records)) (car records))
        (else (assoc key (cdr records)))))

;4.4.4.8 definitions
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

(pattern-match '((? x) (? x) (? y) (? y))
               '(foo foo bar bar)
               '(((? x) . foo)))
(pattern-match '((? x) (? x) (? y) (? y))
               '(bar bar bar bar)
               '(((? x) . foo)))
