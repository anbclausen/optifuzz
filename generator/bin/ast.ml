(** Defines an AST consisting of should-be-constant-time
    nodes. Nodes include all non-branching arithmetic, 
    logical and comparison operators in C other than '/'
    and '%'. Leafs can be the variable 'x', the variable
    'y', an integer, a number between 0 and 64 or a Boolean. *)

type size_expr =
  (* Size - number between 0 and 64 *)
  | SizeLit of int

type bool_expr =
  (* Booleans *)
  | True 
  | False

  (* Logical Operators *)
  | Not of bool_expr

  (* Comparison Operators *)
  | LessThan of arith_expr * arith_expr
  | LessEqual of arith_expr * arith_expr
  | GreaterThan of arith_expr * arith_expr
  | GreaterEqual of arith_expr * arith_expr
  | Equal of arith_expr * arith_expr
  | NotEqual of arith_expr * arith_expr

and arith_expr = 
  (* Input variables *)
  | X
  | Y

  (* Integers *)
  | IntLit of int64

  (* Arithmetic *)
  | Neg of arith_expr
  | Plus of arith_expr * arith_expr
  | Minus of arith_expr * arith_expr
  | Times of arith_expr * arith_expr

type expr =
  | Aexp of arith_expr
  | Bexp of bool_expr

  (* Bitwise Operators *)
  | BitwiseAnd of expr * expr
  | BitwiseOr of expr * expr
  | BitwiseComplement of expr
  | BitwiseXor of expr * expr
  | LeftShift of expr * size_expr
  | RightShift of expr * size_expr

let string_of_sexp = function
  | SizeLit s -> string_of_int s

let rec string_of_bexp = function
  | True -> "true"
  | False -> "false"
  | Not b -> "!" ^ string_of_bexp b
  | LessThan (a1, a2) -> "(" ^ string_of_aexp a1 ^ " < " ^ string_of_aexp a2 ^ ")"
  | LessEqual (a1, a2) -> "(" ^ string_of_aexp a1 ^ " <= " ^ string_of_aexp a2 ^ ")"
  | GreaterThan (a1, a2) -> "(" ^ string_of_aexp a1 ^ " > " ^ string_of_aexp a2 ^ ")"
  | GreaterEqual (a1, a2) -> "(" ^ string_of_aexp a1 ^ " >= " ^ string_of_aexp a2 ^ ")"
  | Equal (a1, a2) -> "(" ^ string_of_aexp a1 ^ " == " ^ string_of_aexp a2 ^ ")"
  | NotEqual (a1, a2) -> "(" ^ string_of_aexp a1 ^ " != " ^ string_of_aexp a2 ^ ")"

and string_of_aexp = function
  | X -> "x"
  | Y -> "y"
  | IntLit i -> Int64.to_string i
  | Neg a -> "-(" ^ string_of_aexp a ^ ")"
  | Plus (a1, a2) -> "(" ^ string_of_aexp a1 ^ " + " ^ string_of_aexp a2 ^ ")"
  | Minus (a1, a2) -> "(" ^ string_of_aexp a1 ^ " - " ^ string_of_aexp a2 ^ ")"
  | Times (a1, a2) -> "(" ^ string_of_aexp a1 ^ " * " ^ string_of_aexp a2 ^ ")"

let rec string_of_expr = function 
  | Aexp a -> string_of_aexp a
  | Bexp b -> string_of_bexp b
  | BitwiseAnd (e1, e2) -> "(" ^ string_of_expr e1 ^ " & " ^ string_of_expr e2 ^ ")"
  | BitwiseOr (e1, e2) -> "(" ^ string_of_expr e1 ^ " | " ^ string_of_expr e2 ^ ")"
  | BitwiseComplement e -> "~" ^ string_of_expr e
  | BitwiseXor (e1, e2) -> "(" ^ string_of_expr e1 ^ " ^ " ^ string_of_expr e2 ^ ")"
  | LeftShift (e, s) -> "(" ^ string_of_expr e ^ " << " ^ string_of_sexp s ^ ")"
  | RightShift (e, s) -> "(" ^ string_of_expr e ^ " >> " ^ string_of_sexp s ^ ")"
