import React from 'react';
import PropTypes from 'prop-types';
import { TbSearch } from 'react-icons/tb';

const SearchBar = ({ value, onChange, placeholder = 'Search...' }) => {
  return (
    <div className="flex items-center bg-white border border-border rounded-xl px-3 py-2 shadow-sm">
      <TbSearch className="text-gray-400" />
      <input
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className="ml-3 w-full outline-none text-sm text-text-primary placeholder:text-text-secondary bg-transparent"
      />
    </div>
  );
};

SearchBar.propTypes = {
  value: PropTypes.string,
  onChange: PropTypes.func,
  placeholder: PropTypes.string,
};

export default SearchBar;
