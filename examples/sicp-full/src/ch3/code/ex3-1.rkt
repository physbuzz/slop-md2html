#lang sicp
(define (make-accumulator n)
  (let ((total n))
    (lambda (arg) 
      (begin
        (set! total (+ total arg))
        total))))

(define A (make-accumulator 5))

(A 10)

(A 10)
