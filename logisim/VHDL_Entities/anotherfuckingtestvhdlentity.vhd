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

ENTITY anotherfuckingtestvhdlentity IS
  PORT (
  ------------------------------------------------------------------------------
  --Insert input ports below
    val        : IN  std_logic_vector(3 DOWNTO 0); -- input vector example
  ------------------------------------------------------------------------------
  --Insert output ports below
    max        : OUT std_logic_vector(3 DOWNTO 0)  -- output vector example
    );
END anotherfuckingtestvhdlentity;

--------------------------------------------------------------------------------
--Complete your VHDL description below
--------------------------------------------------------------------------------

ARCHITECTURE TypeArchitecture OF anotherfuckingtestvhdlentity IS

BEGIN
	max  <= val;
END TypeArchitecture;
