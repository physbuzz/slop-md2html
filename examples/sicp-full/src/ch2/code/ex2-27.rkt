#lang sicp

(define (deep-reverse lst)
  (define (reverse-help lst ret)
    (if (null? lst) 
      ret 
     (reverse-help (cdr lst) 
		   (cons (deep-reverse (car lst)) ret))))
  (if (not (pair? lst)) 
    lst
    (reverse-help lst nil)))
(define x 
  (list (list 1 2) (list 3 4)))

(deep-reverse x)
