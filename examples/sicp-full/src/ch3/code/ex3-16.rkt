#lang sicp

(define (count-pairs x)
  (if (not (pair? x))
      0
      (+ (count-pairs (car x))
         (count-pairs (cdr x))
         1)))

(define list1 '(a b c))
(count-pairs list1)

(define list2 '(a b c))
(set-car! list2 (cdr list2))
(set-cdr! list2 (cddr list2))
(count-pairs list2)

(define list3 '(a b c))
(set-car! (cdr list3) (cddr list3))
(set-car! list3 (cdr list3))
(count-pairs list3)

;; We could do the following, but it would never halt so I'm not doing it
;; (define list4 '(a c))
;; (set-cdr! (cdr list4) list4)
;; (count-pairs list4)
