#lang sicp

(define (make-leaf symbol weight)
  (list 'leaf symbol weight))
(define (leaf? object)
  (eq? (car object) 'leaf))

(define (symbol-leaf x) (cadr x))
(define (weight-leaf x) (caddr x))

(define (left-branch tree) (car tree))
(define (right-branch tree) (cadr tree))

(define (symbols tree)
  (if (leaf? tree)
      (list (symbol-leaf tree))
      (caddr tree)))

(define (weight tree)
  (if (leaf? tree)
      (weight-leaf tree)
      (cadddr tree)))


(define (element-of-list? x lst)
  (cond ((null? lst) false)
        ((equal? x (car lst)) true)
        (else (element-of-list? x (cdr lst)))))


(define (make-code-tree left right)
  (list left
        right
        (append (symbols left)
                (symbols right))
        (+ (weight left) (weight right))))

(define (decode bits tree)
  (define (decode-1 bits current-branch)
    (if (null? bits)
        '()
        (let ((next-branch
               (choose-branch
                (car bits)
                current-branch)))
          (if (leaf? next-branch)
              (cons
               (symbol-leaf next-branch)
               (decode-1 (cdr bits) tree))
              (decode-1 (cdr bits)
                        next-branch)))))
  (decode-1 bits tree))

(define (choose-branch bit branch)
  (cond ((= bit 0) (left-branch branch))
        ((= bit 1) (right-branch branch))
        (else (error "bad bit:
               CHOOSE-BRANCH" bit))))

(define (adjoin-set x set)
  (cond ((null? set) (list x))
        ((< (weight x) (weight (car set))) 
         (cons x set))
        (else 
         (cons (car set)
               (adjoin-set x (cdr set))))))

(define (make-leaf-set pairs)
  (if (null? pairs)
      '()
      (let ((pair (car pairs)))
        (adjoin-set 
         (make-leaf (car pair)    ; symbol
                    (cadr pair))  ; frequency
         (make-leaf-set (cdr pairs))))))

(define sample-tree
  (make-code-tree 
   (make-leaf 'A 4)
   (make-code-tree
    (make-leaf 'B 2)
    (make-code-tree 
     (make-leaf 'D 1)
     (make-leaf 'C 1)))))

(define sample-message 
  '(0 1 1 0 0 1 0 1 0 1 1 1 0))

(define (encode message tree)
  (if (null? message)
      '()
      (append 
       (encode-symbol (car message) 
                      tree)
       (encode (cdr message) tree))))

(define (encode-symbol symbol tree)
  (cond
    ((leaf? tree) 
                (if 
                  (equal? (symbol-leaf tree) symbol) '() 
                  (error "symbol not in tree " symbol)))
    ((element-of-list? symbol (symbols (left-branch tree))) 
                    (cons '0 (encode-symbol symbol (left-branch tree))))
    ((element-of-list? symbol (symbols (right-branch tree))) 
                    (cons '1 (encode-symbol symbol (right-branch tree))))
    (else (error "symbol not in tree" symbol))))

(define (generate-huffman-tree pairs)
  (successive-merge
   (make-leaf-set pairs)))

    ;; merge the symbols of the first two elements of the list
    ;; add the weights
    ;; make the tree
(define (successive-merge tree-list) 
  (if (= 1 (length tree-list)) (car tree-list)
    (let ((a (car tree-list)) 
          (b (cadr tree-list)) 
          (rest (cddr tree-list)))
      (successive-merge (adjoin-set (make-code-tree a b) rest)))))

(define my-tree (generate-huffman-tree '((a 2) (na 16) (boom 1) (sha 3) (get 2) (yip 9) (job 2) (wah 1))))


(define (pow2-tree n2)
  (define (pow2-list n arg)
    (if (= n 0) nil
      (cons (list (- n2 n) arg) (pow2-list (- n 1) (* 2 arg)))))
  (generate-huffman-tree (pow2-list n2 1)))

(pow2-tree 5)
(pow2-tree 10)
    
















