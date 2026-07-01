#lang sicp

(define (cont-frac n d k)
  (define (bottom-up kprime val)
    (if (= kprime 0)
      val
      (bottom-up (- kprime 1) 
		 (/ (n kprime) 
      		    (+ (d kprime) val)))))
  (bottom-up k 0))

; `1, 2, 1, 1, 4, 1, 1, 6, 1, 1, 8, ...`
(let ((n (lambda (k) 1.0) )
      (d (lambda (k) 
	         (let ((m (remainder k 3)))
	    	 (cond ((= m 1) 1)
	               ((= m 2) (* 2 (/ (+ k 1) 3)))
		       (else 1))))))
  (display "11 terms: ")
  (display (cont-frac n d 11))
  (newline)
  (display "Exact   : 0.71828182845904"))
