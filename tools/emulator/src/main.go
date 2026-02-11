package main

import "fmt"

func getOperands(instructionType int, p1, p2, p3 int) map[string]interface{} {
	result := make(map[string]interface{})

	switch instructionType {
	case 1:
		// pipeline reg 1: a4 b4
		// pipeline reg 1: aluOP4 res4
		result["A"] = p1 & 0x07
		// result["B"] := (p.p1 >> 4) & 0x07 // is this supposed to shift 3 bits??
		result["B"] = (p2 >> 4) & 0x07 // is this supposed to shift 3 bits??
		result["Res"] = p3 & 0x07
	default:
		fmt.Println("Owned by skill issue")
	}

	return result
}

func main() {
	result := getOperands(1, 9, 9, 9)
	fmt.Println(result)
	fmt.Println(result["A"].(int) + result["B"].(int))
	// Expected: map[A:1 B:0 Res:1], sum: 1

	result = getOperands(1, 42, 87, 23)
	fmt.Println(result)
	fmt.Println(result["A"].(int) + result["B"].(int))
	// Expected: map[A:2 B:5 Res:7], sum: 7

	result = getOperands(1, 255, 255, 255)
	fmt.Println(result)
	fmt.Println(result["A"].(int) + result["B"].(int))
	// Expected: map[A:7 B:7 Res:7], sum: 14
}
