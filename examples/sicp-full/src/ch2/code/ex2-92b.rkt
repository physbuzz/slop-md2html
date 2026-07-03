#lang sicp

;; insertion sort from https://gist.github.com/miyukino/5652107
(define (insert L M comp)
	(if (null? L) M
		(if (null? M) L
			(if (comp (car L) (car M))
				(cons (car L) (insert (cdr L) M comp))
				(cons (car M) (insert (cdr M) L comp))))))
(define (insertionsort L comp)
	(if (null? L) '()
		(insert (list (car L)) (insertionsort (cdr L) comp) comp)))
(define sort insertionsort)

(define (symbol<? s1 s2)
  (string<? (symbol->string s1) (symbol->string s2)))
(define (symbol=? s1 s2)
  (string=? (symbol->string s1) (symbol->string s2)))

;; Lexicographic ordering on monomials. If we want the highest order monomial as the first element, we 
;; could sort from least to greatest where we define '() to be the greatest element, so this definition
;; might look a bit backwards.
(define (single-order<? so1 so2)
  (or (symbol<? (car so1) (car so2))
      (< (cadr so2) (cadr so1))))
(define (order<? o1 o2)
  (cond 
    ((null? o1) #f)
    ((null? o2) #t)
    ((< (length o2) (length o1)) #t)
    ((single-order<? (car o1) (car o2)) #t)
    ((single-order<? (car o2) (car o1)) #f)
    (else (order<? (cdr o1) (cdr o2)))))

(define l1 '((x 2) (y 1)))
(define l2 '((x 2) (y 2)))
(define l3 (sort '((x 2) (y 2) (foobar 10) (a 4)) single-order<?))
(define l4 '())
(sort (list l1 l2 l3 l4)  order<?)
