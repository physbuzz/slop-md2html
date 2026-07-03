#lang sicp
(define (square x) (* x x))

;; Stubbornly trying to use tail recursion. This is a stupid idea, 
;; but there you go.
(define (square-list1 lst)
  (define (squar-list lst ret)
    (if (null? lst) 
     (reverse ret)
     (squar-list 
	       (cdr lst) 
	       (cons (square (car lst)) ret))))
  (squar-list lst nil))

(define (square-list2 items)
  (if (null? items)
      nil
      (cons (square (car items)) 
	    (square-list2 (cdr items)))))

(define (square-list3 items)
  (map square items))
(square-list1 (list 1 2 3 4 5 6 7))
(square-list2 (list 1 2 3 4 5 6 7))
(square-list3 (list 1 2 3 4 5 6 7))
