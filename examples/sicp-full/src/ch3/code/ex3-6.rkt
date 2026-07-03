#lang sicp
(define A 1664525)
(define B 1013904223)
(define C 4294967296)
(define random-init 1000000)

(define (rand-update arg)
  (remainder (+ (* A arg) B) C))
(define rand
  (let ((x random-init))
    (lambda (m) 
      (cond ((eq? m 'generate)
             (set! x (rand-update x)) x)
            ((eq? m 'reset)
             (lambda (arg) (set! x arg)))
            (else (error "invalid message" m))))))


(rand 'generate)
(rand 'generate)
(rand 'generate)
(display "Resetting") (newline)
((rand 'reset) 12345)
(rand 'generate)
(rand 'generate)
(display "Resetting") (newline)
((rand 'reset) 12345)
(rand 'generate)
(rand 'generate)
