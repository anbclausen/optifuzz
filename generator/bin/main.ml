open Ast
open Generator
open Distribution
open Write 

let n = Sys.argv.(1) |> int_of_string
let seed = Sys.argv.(2) |> int_of_string

(** Generates a random AST from [seed]. *)
let rec generate_random_ast seed =
  let state = Random.State.make [|seed|] in 
  let distribution = random_distribution seed in
  let ast = Lazy.force (random_expr state 0 distribution) in
  let prg = program (string_of_expr ast) in
  (* Body of the function should contain both x and y *)
  if String.contains_from prg 58 'x' && String.contains_from prg 58 'y' then
    let filename = "generated/" ^ (string_of_int seed) ^ ".c" in
    write_file filename prg
  else 
    generate_random_ast (seed + 1)
  

let () = 
  if seed = 0 then
    (Random.self_init ();
    for _ = 1 to n do
      let random_seed = Random.bits () in
      generate_random_ast random_seed
    done)
  else
    generate_random_ast seed
    