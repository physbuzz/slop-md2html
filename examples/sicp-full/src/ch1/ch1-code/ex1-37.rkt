#lang sicp

; Iterative loop for calculating continued fractions: start at the bottom
; value1 = (/ ( n k) (d k))
; value2 = (/ ( n (- k 1)) (+ (d (- k 1)) value1))
; value3 = (/ ( n (- k 2)) (+ (d (- k 2)) value2))
(define (cont-frac n d k)
  (define (bottom-up kprime val)
    (if (= kprime 0)
      val
      (bottom-up (- kprime 1) 
		 (/ (n kprime) 
      		    (+ (d kprime) val)))))
  (bottom-up k 0))

; (/ (n 1) (+ (d 1) (terms 2 k)))
(define (cont-frac-recursive n d k)
  (define (top-down kprime)
    (if (= kprime k)
      (/ (n kprime) (d kprime))
      (/ (n kprime) (+ (d kprime) (top-down (+ kprime 1))))))
  (top-down 1))


(cont-frac (lambda (i) 1) (lambda (i) 1) 6)
(cont-frac-recursive (lambda (i) 1) (lambda (i) 1) 6)

(define tolerance 0.00005)
(define (n-accuracy f exact n)
  (if (< (abs (- (f n) exact)) tolerance)
    n
    (n-accuracy f exact (+ n 1))))

(let ((n (n-accuracy 
	(lambda (k) (cont-frac (lambda (i) 1) (lambda (i) 1) k))
	(/ (- (sqrt 5.0) 1) 2)
	1)))
  (display "n required for an accuracy of ")
  (display tolerance) 
  (display " is ")
  (display n)
  (newline)
  (display 0.6180339887498)
  (newline)
  (cont-frac (lambda (i) 1.0) (lambda (i) 1.0) n))
