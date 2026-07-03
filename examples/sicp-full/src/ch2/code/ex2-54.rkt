#lang sicp

(define (equal? a b)
  (or (and (symbol? a) (symbol? b) (eq? a b))
      (and (null? a) (null? b))
      (and (pair? a) (pair? b) 
           (equal? (car a) (car b))
           (equal? (cdr a) (cdr b)))))

;;Some test cases:
(equal? '(this is a list) 
        '(this is a list))
(equal? '(this is a list) 
        '(this (is a) list))
(equal? '(this (is a) list) 
        '(this (is a) list))
(equal? 'a '(a b c))

;; Failure case! 
(equal? (list 1 2 3) (list 1 2 3))
