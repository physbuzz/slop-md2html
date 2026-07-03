#lang sicp

(define (make-account balance pw)
  (define (withdraw amount)
    (if (>= balance amount)
        (begin (set! balance
                     (- balance amount))
               balance)
        "Insufficient funds"))
  (define (deposit amount)
    (set! balance (+ balance amount))
    balance)
  (define (errorfunc . args) 
    "Incorrect Password")
  (define (dispatch pw-arg m)
    (cond ((not (eq? pw pw-arg)) errorfunc)
          ((eq? m 'withdraw) withdraw)
          ((eq? m 'deposit) deposit)
          (else (error "Unknown request:
                 MAKE-ACCOUNT" m))))
  dispatch)

(define (make-joint orig-account orig-password new-password)
  (lambda (pw-arg m)
    (if (eq? pw-arg new-password)
      (orig-account orig-password m)
      (lambda args "Incorrect password"))))

(define peter-acc 
  (make-account 100 'peter-password))

(define paul-acc
  (make-joint peter-acc 
              'peter-password 
              'paul-password))

((peter-acc 'peter-password 'withdraw) 10)
;; 90

((paul-acc 'paul-password 'withdraw) 10)
;; 80

((paul-acc 'peter-password 'withdraw) 10)
;; "Incorrect password"
