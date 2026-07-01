#lang sicp

(define (f-rec n)
  (if (< n 3) 
     n
     (+ (f-rec (- n 1)) 
        (* 2 (f-rec (- n 2))) 
        (* 3 (f-rec (- n 3))))))

(f-rec 1)
(f-rec 2)
(f-rec 3)
(f-rec 4)
(f-rec 5)
(f-rec 6)


