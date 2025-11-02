--------------------------------------------------------------------------------
-- Project :
-- File    :
-- Autor   :
-- Date    :
--
--------------------------------------------------------------------------------
-- Description :
--
--------------------------------------------------------------------------------

LIBRARY ieee;
USE ieee.std_logic_1164.all;
use ieee.NUMERIC_STD.all;

ENTITY RegisterFile IS
	port(
		----------------------------------------------------------------
		-- Inputs
		A_addr: in std_logic_vector(2 downto 0); -- 3-bit input
		B_addr: in std_logic_vector(2 downto 0); -- 3-bit input
		Write_addr: in std_logic_vector(2 downto 0); -- 3-bit input
		data: in std_logic_vector(7 downto 0);
		reset: in std_logic;
		clock: in std_logic;

		----------------------------------------------------------------
		-- Outputs
		A_output: out std_logic_vector(7 downto 0);
		B_output: out std_logic_vector(7 downto 0)
		);
END RegisterFile;

ARCHITECTURE TypeArchitecture OF RegisterFile IS
	type regArray is array(0 to 7) of STD_LOGIC_VECTOR(7 downto 0);
	signal regs: regArray  := (others => (others => '0'));
BEGIN

-- Write process
	process(clock,reset)
	begin
		if reset = '1' then
			regs <= (others => (others => '0'));
		elsif rising_edge(clock) then
			regs(to_integer(unsigned(Write_addr)))  <= data;
		end if;
	end process;

-- Read ports
	A_output  <=  regs(to_integer(unsigned(A_addr)));
	B_output  <=  regs(to_integer(unsigned(B_addr)));

END TypeArchitecture;
