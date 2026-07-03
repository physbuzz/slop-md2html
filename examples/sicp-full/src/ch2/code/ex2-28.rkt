#lang sicp


;;Way too complicated!
(define (append-at lst)
  (define (listify arg)
    (if (pair? arg) arg (list arg)))
  (if (or (null? lst) (not (pair? lst))) lst
    (let ((a (car lst)) (b (cdr lst)))
      (append (listify (car lst)) (append-at (cdr lst))))))
(define (fringe lst) 
  (if (pair? lst)
    (append-at (map fringe lst))
    lst))

;;Solution from Solving SICP
(define (fringe2 tree)
  (define (fringe-iter tree accumulator)
    (cond ((null? tree) tree)
          ((not (pair? tree)) (list tree))
	  (else (append accumulator
		  (fringe-iter (car tree) nil)
		  (fringe-iter (cdr tree) nil)))))
  (fringe-iter tree nil))

;;Yet simpler solution from https://billthelizard.blogspot.com/2011/02/sicp-228-flattening-nested-lists.html
;; The way I was trying to use map for fringe-v1 made things more complicated.
(define (fringe3 tree)
  (cond ((null? tree) nil)
        ((not (pair? tree)) (list tree))
	(else (append (fringe (car tree))
	              (fringe (cdr tree))))))

(define x
  (list (list 1 2) (list 3 4)))

(fringe x)
(fringe2 x)
(fringe3 x)
(fringe (list x x))
(fringe2 (list x x))
(fringe3 (list x x))
